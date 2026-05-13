"""
Generates realistic Indian election data for the bias audit system.
Based on real ECI statistical patterns from Lok Sabha elections 1999-2024.
"""

import random
import numpy as np
from datetime import datetime, timedelta

STATES = [
    "Uttar Pradesh", "Maharashtra", "West Bengal", "Bihar", "Madhya Pradesh",
    "Tamil Nadu", "Rajasthan", "Karnataka", "Gujarat", "Andhra Pradesh",
    "Odisha", "Telangana", "Kerala", "Jharkhand", "Assam",
    "Punjab", "Chhattisgarh", "Haryana", "Delhi", "Uttarakhand"
]

PARTIES = ["BJP", "INC", "SP", "BSP", "TMC", "DMK", "AIADMK", "NCP", "CPI(M)", "JD(U)", "RJD", "TDP", "YSR CP", "AAP", "Independent"]

CASTE_CATEGORIES = ["General", "OBC", "SC", "ST"]

ELECTIONS = [
    {"year": 1999, "total_seats": 543},
    {"year": 2004, "total_seats": 543},
    {"year": 2009, "total_seats": 543},
    {"year": 2014, "total_seats": 543},
    {"year": 2019, "total_seats": 543},
    {"year": 2024, "total_seats": 543},
]

# Real-world based stats: female candidate share per election (growing trend)
FEMALE_CANDIDATE_SHARE = {1999: 0.07, 2004: 0.08, 2009: 0.09, 2014: 0.09, 2019: 0.10, 2024: 0.13}
FEMALE_WIN_RATE = {1999: 0.34, 2004: 0.37, 2009: 0.40, 2014: 0.36, 2019: 0.39, 2024: 0.42}
MALE_WIN_RATE = {1999: 0.87, 2004: 0.85, 2009: 0.84, 2014: 0.86, 2019: 0.88, 2024: 0.87}

# Turnout by region (real patterns)
REGIONAL_TURNOUT = {
    "North": {1999: 0.52, 2004: 0.55, 2009: 0.53, 2014: 0.60, 2019: 0.62, 2024: 0.63},
    "South": {1999: 0.63, 2004: 0.68, 2009: 0.65, 2014: 0.70, 2019: 0.72, 2024: 0.73},
    "East":  {1999: 0.58, 2004: 0.60, 2009: 0.57, 2014: 0.64, 2019: 0.66, 2024: 0.67},
    "West":  {1999: 0.55, 2004: 0.57, 2009: 0.54, 2014: 0.61, 2019: 0.63, 2024: 0.64},
    "NE":    {1999: 0.70, 2004: 0.72, 2009: 0.69, 2014: 0.74, 2019: 0.76, 2024: 0.77},
}

STATE_REGION = {
    "Uttar Pradesh": "North", "Bihar": "North", "Rajasthan": "North",
    "Madhya Pradesh": "North", "Delhi": "North", "Haryana": "North",
    "Punjab": "North", "Uttarakhand": "North",
    "Tamil Nadu": "South", "Karnataka": "South", "Kerala": "South",
    "Andhra Pradesh": "South", "Telangana": "South",
    "West Bengal": "East", "Odisha": "East", "Jharkhand": "East", "Assam": "East",
    "Maharashtra": "West", "Gujarat": "West", "Chhattisgarh": "West",
    "NCP": "West",
}

PARTY_FEMALE_SHARE = {
    "BJP":   {1999: 0.08, 2004: 0.09, 2009: 0.08, 2014: 0.09, 2019: 0.13, 2024: 0.14},
    "INC":   {1999: 0.10, 2004: 0.11, 2009: 0.12, 2014: 0.14, 2019: 0.15, 2024: 0.17},
    "TMC":   {1999: 0.22, 2004: 0.24, 2009: 0.26, 2014: 0.28, 2019: 0.30, 2024: 0.32},
    "SP":    {1999: 0.04, 2004: 0.04, 2009: 0.05, 2014: 0.05, 2019: 0.06, 2024: 0.08},
    "BSP":   {1999: 0.07, 2004: 0.08, 2009: 0.09, 2014: 0.09, 2019: 0.10, 2024: 0.12},
    "DMK":   {1999: 0.09, 2004: 0.10, 2009: 0.10, 2014: 0.11, 2019: 0.12, 2024: 0.15},
}

SC_WIN_RATE_MULTIPLIER = 0.92
ST_WIN_RATE_MULTIPLIER = 0.88
OBC_WIN_RATE_MULTIPLIER = 0.95
GENERAL_WIN_RATE_MULTIPLIER = 1.05


def get_region(state):
    return STATE_REGION.get(state, "North")


def generate_elections_collection():
    docs = []
    for e in ELECTIONS:
        year = e["year"]
        for state in STATES:
            region = get_region(state)
            base_turnout = REGIONAL_TURNOUT.get(region, {}).get(year, 0.60)
            male_turnout = base_turnout + random.uniform(-0.02, 0.04)
            female_turnout = base_turnout - random.uniform(0.01, 0.06)
            docs.append({
                "year": year,
                "state": state,
                "region": region,
                "total_seats": random.randint(4, 80),
                "total_votes_polled": random.randint(500000, 45000000),
                "voter_turnout_pct": round(base_turnout + random.uniform(-0.03, 0.03), 3),
                "male_turnout_pct": round(male_turnout, 3),
                "female_turnout_pct": round(female_turnout, 3),
                "turnout_gender_gap": round(male_turnout - female_turnout, 3),
                "election_type": "General",
                "created_at": datetime(year, 4, 15)
            })
    return docs


def generate_candidates_collection():
    docs = []
    for e in ELECTIONS:
        year = e["year"]
        total_candidates = random.randint(7000, 8500)
        female_share = FEMALE_CANDIDATE_SHARE[year]
        
        for i in range(total_candidates):
            state = random.choice(STATES)
            party = random.choice(PARTIES)
            is_female = random.random() < female_share
            gender = "Female" if is_female else "Male"
            caste = random.choices(CASTE_CATEGORIES, weights=[30, 40, 20, 10])[0]
            
            # Win probability based on gender and caste
            base_win = FEMALE_WIN_RATE[year] if is_female else MALE_WIN_RATE[year]
            caste_mult = {"General": GENERAL_WIN_RATE_MULTIPLIER, "OBC": OBC_WIN_RATE_MULTIPLIER,
                          "SC": SC_WIN_RATE_MULTIPLIER, "ST": ST_WIN_RATE_MULTIPLIER}[caste]
            win_prob = min(base_win * caste_mult * random.uniform(0.8, 1.2), 0.95)
            won = random.random() < (win_prob * 0.15)  # normalize to ~14% win rate across all
            
            docs.append({
                "election_year": year,
                "state": state,
                "region": get_region(state),
                "party": party,
                "gender": gender,
                "caste_category": caste,
                "votes": random.randint(5000, 800000),
                "won": won,
                "deposit_forfeited": not won and random.random() < 0.6,
                "created_at": datetime(year, 5, 1)
            })
    return docs


def compute_bias_metrics(year, candidates_docs):
    year_cands = [c for c in candidates_docs if c["election_year"] == year]
    
    # Gender metrics
    male_cands = [c for c in year_cands if c["gender"] == "Male"]
    female_cands = [c for c in year_cands if c["gender"] == "Female"]
    
    male_win_rate = sum(1 for c in male_cands if c["won"]) / max(len(male_cands), 1)
    female_win_rate = sum(1 for c in female_cands if c["won"]) / max(len(female_cands), 1)
    female_candidate_share = len(female_cands) / max(len(year_cands), 1)
    win_rate_gap = male_win_rate - female_win_rate
    
    # Caste metrics
    caste_win_rates = {}
    for cat in CASTE_CATEGORIES:
        cat_cands = [c for c in year_cands if c["caste_category"] == cat]
        caste_win_rates[cat] = round(sum(1 for c in cat_cands if c["won"]) / max(len(cat_cands), 1), 4)
    
    max_caste_gap = max(caste_win_rates.values()) - min(caste_win_rates.values())
    
    # Regional turnout (use election docs for this)
    regional_gaps = REGIONAL_TURNOUT
    ne_south_gap = abs(
        REGIONAL_TURNOUT["NE"].get(year, 0.70) - REGIONAL_TURNOUT["South"].get(year, 0.65)
    )
    north_south_gap = abs(
        REGIONAL_TURNOUT["North"].get(year, 0.55) - REGIONAL_TURNOUT["South"].get(year, 0.65)
    )
    
    # Party female share
    party_metrics = {}
    for party in ["BJP", "INC", "TMC", "SP", "BSP"]:
        party_cands = [c for c in year_cands if c["party"] == party]
        if party_cands:
            f_share = sum(1 for c in party_cands if c["gender"] == "Female") / len(party_cands)
            party_metrics[party] = {
                "total_candidates": len(party_cands),
                "female_share": round(f_share, 4),
                "female_win_rate": round(
                    sum(1 for c in party_cands if c["gender"] == "Female" and c["won"]) / 
                    max(sum(1 for c in party_cands if c["gender"] == "Female"), 1), 4
                )
            }
    
    # Overall bias score (weighted average of all gaps, normalized 0-1)
    gender_bias = min(win_rate_gap / 0.60, 1.0)
    representation_bias = min((0.5 - female_candidate_share) / 0.5, 1.0)
    caste_bias = min(max_caste_gap / 0.20, 1.0)
    regional_bias = min(north_south_gap / 0.20, 1.0)
    
    bias_score = round(
        0.35 * gender_bias + 
        0.30 * representation_bias + 
        0.20 * caste_bias + 
        0.15 * regional_bias, 4
    )
    
    return {
        "election_year": year,
        "computed_at": datetime(year, 6, 1),
        "total_candidates": len(year_cands),
        "fairness_metrics": {
            "gender": {
                "male_candidate_count": len(male_cands),
                "female_candidate_count": len(female_cands),
                "female_candidate_share": round(female_candidate_share, 4),
                "male_win_rate": round(male_win_rate, 4),
                "female_win_rate": round(female_win_rate, 4),
                "win_rate_gap": round(win_rate_gap, 4),
            },
            "caste": {
                "win_rates_by_category": caste_win_rates,
                "max_gap": round(max_caste_gap, 4),
            },
            "regional": {
                "north_turnout": REGIONAL_TURNOUT["North"].get(year, 0.55),
                "south_turnout": REGIONAL_TURNOUT["South"].get(year, 0.65),
                "east_turnout": REGIONAL_TURNOUT["East"].get(year, 0.58),
                "west_turnout": REGIONAL_TURNOUT["West"].get(year, 0.57),
                "ne_turnout": REGIONAL_TURNOUT["NE"].get(year, 0.70),
                "north_south_gap": round(north_south_gap, 4),
            },
            "party_representation": party_metrics,
        },
        "bias_score": bias_score,
        "bias_flag": bias_score > 0.35,
        "component_scores": {
            "gender_bias": round(gender_bias, 4),
            "representation_bias": round(representation_bias, 4),
            "caste_bias": round(caste_bias, 4),
            "regional_bias": round(regional_bias, 4),
        }
    }


def generate_alerts(audit_logs):
    alerts = []
    thresholds = {
        "gender.win_rate_gap": 0.30,
        "gender.female_candidate_share": 0.15,
        "caste.max_gap": 0.10,
        "regional.north_south_gap": 0.08,
        "overall.bias_score": 0.40,
    }
    
    for log in audit_logs:
        year = log["election_year"]
        metrics = log["fairness_metrics"]
        
        checks = [
            ("gender.win_rate_gap", metrics["gender"]["win_rate_gap"],
             "HIGH" if metrics["gender"]["win_rate_gap"] > 0.40 else "MEDIUM"),
            ("gender.female_candidate_share", metrics["gender"]["female_candidate_share"],
             "HIGH" if metrics["gender"]["female_candidate_share"] < 0.10 else "MEDIUM",
             True),  # True = flag when BELOW threshold
            ("caste.max_gap", metrics["caste"]["max_gap"],
             "MEDIUM"),
            ("regional.north_south_gap", metrics["regional"]["north_south_gap"],
             "LOW"),
            ("overall.bias_score", log["bias_score"],
             "HIGH" if log["bias_score"] > 0.45 else "MEDIUM"),
        ]
        
        for check in checks:
            metric_name, actual_val = check[0], check[1]
            severity = check[2]
            below = len(check) > 3 and check[3]
            threshold = thresholds.get(metric_name, 0.3)
            
            breached = (actual_val < threshold) if below else (actual_val > threshold)
            if breached:
                alerts.append({
                    "election_year": year,
                    "metric": metric_name,
                    "threshold": threshold,
                    "actual_value": round(actual_val, 4),
                    "direction": "below" if below else "above",
                    "severity": severity,
                    "resolved": random.random() < 0.3,
                    "created_at": datetime(year, 6, 2),
                    "description": f"Election {year}: {metric_name} = {actual_val:.3f} ({'below' if below else 'above'} threshold {threshold})"
                })
    
    return alerts
