"""
MongoDB Atlas connection and data seeding for Indian Election Bias Audit System.
Handles all database operations via PyMongo.
"""

import os
import streamlit as st
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from utils.data_generator import (
    generate_elections_collection,
    generate_candidates_collection,
    compute_bias_metrics,
    generate_alerts,
    ELECTIONS,
)


def get_mongo_uri():
    from dotenv import load_dotenv
    load_dotenv(override=True)
    uri = os.getenv("MONGODB_URI", "")
    if not uri and hasattr(st, "secrets"):
        try:
            uri = st.secrets.get("MONGODB_URI", "")
        except Exception:
            pass
    return uri


@st.cache_resource(show_spinner=False)
def get_database():
    uri = get_mongo_uri()
    if not uri:
        return None, "No MongoDB URI configured. Using demo mode with in-memory data."
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        db = client["election_bias_audit"]
        return db, None
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        return None, f"MongoDB connection failed: {str(e)}"
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"


def seed_database(db):
    """Seed all 4 collections if they are empty."""
    results = {"elections": 0, "candidates": 0, "audit_logs": 0, "alerts": 0}
    
    if db["elections"].count_documents({}) == 0:
        docs = generate_elections_collection()
        db["elections"].insert_many(docs)
        db["elections"].create_index([("year", ASCENDING), ("state", ASCENDING)])
        results["elections"] = len(docs)
    
    if db["candidates"].count_documents({}) == 0:
        docs = generate_candidates_collection()
        db["candidates"].insert_many(docs)
        db["candidates"].create_index([("election_year", ASCENDING)])
        db["candidates"].create_index([("gender", ASCENDING)])
        results["candidates"] = len(docs)
    
    if db["audit_logs"].count_documents({}) == 0:
        all_candidates = list(db["candidates"].find({}, {"_id": 0}))
        logs = [compute_bias_metrics(e["year"], all_candidates) for e in ELECTIONS]
        db["audit_logs"].insert_many(logs)
        db["audit_logs"].create_index([("election_year", ASCENDING)])
        results["audit_logs"] = len(logs)
    
    if db["alerts"].count_documents({}) == 0:
        audit_logs = list(db["audit_logs"].find({}, {"_id": 0}))
        alerts = generate_alerts(audit_logs)
        db["alerts"].insert_many(alerts)
        db["alerts"].create_index([("severity", ASCENDING), ("resolved", ASCENDING)])
        results["alerts"] = len(alerts)
    
    return results


# ── Query helpers ────────────────────────────────────────────────────────────

def get_audit_logs(db):
    if db is None:
        return _demo_audit_logs()
    return list(db["audit_logs"].find({}, {"_id": 0}).sort("election_year", ASCENDING))


def get_elections(db):
    if db is None:
        return _demo_elections()
    return list(db["elections"].find({}, {"_id": 0}))


def get_alerts(db, severity=None, resolved=None):
    if db is None:
        return _demo_alerts()
    query = {}
    if severity:
        query["severity"] = severity
    if resolved is not None:
        query["resolved"] = resolved
    return list(db["alerts"].find(query, {"_id": 0}).sort("election_year", ASCENDING))


def get_party_metrics(db):
    if db is None:
        return _demo_party_metrics()
    pipeline = [
        {"$group": {
            "_id": {"party": "$party", "year": "$election_year"},
            "total": {"$sum": 1},
            "female": {"$sum": {"$cond": [{"$eq": ["$gender", "Female"]}, 1, 0]}},
            "winners": {"$sum": {"$cond": ["$won", 1, 0]}},
            "female_winners": {"$sum": {"$cond": [
                {"$and": [{"$eq": ["$gender", "Female"]}, "$won"]}, 1, 0
            ]}},
        }},
        {"$project": {
            "party": "$_id.party",
            "year": "$_id.year",
            "total": 1,
            "female": 1,
            "female_share": {"$divide": ["$female", "$total"]},
            "win_rate": {"$divide": ["$winners", "$total"]},
        }},
        {"$sort": {"year": 1, "total": -1}}
    ]
    return list(db["candidates"].aggregate(pipeline))


def get_state_bias(db):
    if db is None:
        return _demo_state_bias()
    pipeline = [
        {"$group": {
            "_id": "$state",
            "total": {"$sum": 1},
            "female": {"$sum": {"$cond": [{"$eq": ["$gender", "Female"]}, 1, 0]}},
            "male_wins": {"$sum": {"$cond": [
                {"$and": [{"$eq": ["$gender", "Male"]}, "$won"]}, 1, 0
            ]}},
            "female_wins": {"$sum": {"$cond": [
                {"$and": [{"$eq": ["$gender", "Female"]}, "$won"]}, 1, 0
            ]}},
            "male_total": {"$sum": {"$cond": [{"$eq": ["$gender", "Male"]}, 1, 0]}},
            "female_total": {"$sum": {"$cond": [{"$eq": ["$gender", "Female"]}, 1, 0]}},
        }},
        {"$project": {
            "state": "$_id",
            "female_share": {"$divide": ["$female", "$total"]},
            "male_win_rate": {"$divide": ["$male_wins", {"$max": ["$male_total", 1]}]},
            "female_win_rate": {"$divide": ["$female_wins", {"$max": ["$female_total", 1]}]},
        }},
        {"$addFields": {
            "win_rate_gap": {"$subtract": ["$male_win_rate", "$female_win_rate"]}
        }},
        {"$sort": {"win_rate_gap": -1}}
    ]
    return list(db["candidates"].aggregate(pipeline))


# ── Demo data (no MongoDB) ────────────────────────────────────────────────────

def _demo_audit_logs():
    all_candidates = generate_candidates_collection()
    logs = [compute_bias_metrics(e["year"], all_candidates) for e in ELECTIONS]
    return logs


def _demo_elections():
    return generate_elections_collection()


def _demo_alerts():
    logs = _demo_audit_logs()
    return generate_alerts(logs)


def _demo_party_metrics():
    import random
    rows = []
    for year in [1999, 2004, 2009, 2014, 2019, 2024]:
        for party in ["BJP", "INC", "TMC", "SP", "BSP"]:
            total = random.randint(200, 400)
            female = int(total * random.uniform(0.05, 0.20))
            rows.append({
                "party": party,
                "year": year,
                "total": total,
                "female": female,
                "female_share": female / total,
                "win_rate": random.uniform(0.10, 0.25),
            })
    return rows


def _demo_state_bias():
    import random
    from utils.data_generator import STATES
    rows = []
    for state in STATES:
        male_win = random.uniform(0.12, 0.18)
        female_win = random.uniform(0.04, 0.12)
        rows.append({
            "state": state,
            "female_share": random.uniform(0.06, 0.14),
            "male_win_rate": male_win,
            "female_win_rate": female_win,
            "win_rate_gap": male_win - female_win,
        })
    return sorted(rows, key=lambda x: -x["win_rate_gap"])
