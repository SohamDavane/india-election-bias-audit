"""
Page 5: MongoDB Explorer — raw document viewer & query showcase
"""
import streamlit as st
import json
from utils.db import get_database, get_audit_logs, get_alerts, get_elections

st.set_page_config(page_title="MongoDB Explorer · India Election Audit", page_icon="🍃", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=IBM+Plex+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'Syne', sans-serif; }
section[data-testid="stSidebar"] { background: #0D0D14; border-right: 1px solid #1E1E2E; }
section[data-testid="stSidebar"] * { color: #C8C8E0 !important; }
div[data-testid="stAppViewContainer"] { background: #08080F; }
div[data-testid="block-container"] { background: #08080F; }
.section-head {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem;
    color: #6B6B9A; text-transform: uppercase; letter-spacing: 0.12em;
    border-bottom: 1px solid #1E1E35; padding-bottom: 0.5rem; margin-bottom: 1rem;
}
.page-title { font-size: 2rem; font-weight: 800; color: #F0F0FF; margin-bottom: 0.3rem; }
.page-sub { font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; color: #6B6B9A; margin-bottom: 1.5rem; }
.doc-card {
    background: #0A0A12; border: 1px solid #1E1E35; border-radius: 8px;
    padding: 1rem; margin-bottom: 0.8rem; font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem; color: #9090B8; overflow-x: auto;
}
.query-card {
    background: #080810; border: 1px solid #2A2A45; border-radius: 8px;
    padding: 1.2rem; margin-bottom: 1rem; border-left: 3px solid #4299E1;
}
.query-title { font-size: 1rem; font-weight: 700; color: #F0F0FF; margin-bottom: 0.3rem; }
.query-desc { font-size: 0.83rem; color: #8888AA; margin-bottom: 0.8rem; }
</style>
""", unsafe_allow_html=True)

db, db_error = get_database()

st.markdown('<div class="page-title">🍃 MongoDB Explorer</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Raw document viewer — inspect collection schemas and showcase queries</div>', unsafe_allow_html=True)

collection_choice = st.selectbox(
    "Browse collection",
    ["audit_logs", "elections", "alerts"],
    format_func=lambda x: f"db.{x}"
)

# ─── Document viewer ──────────────────────────────────────────────────────────
st.markdown(f'<div class="section-head">db.{collection_choice} — sample documents</div>', unsafe_allow_html=True)

def serialize_doc(doc):
    from datetime import datetime
    def convert(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, '__str__'):
            return str(obj)
        return obj
    
    result = {}
    for k, v in doc.items():
        if k == "_id":
            continue
        if isinstance(v, datetime):
            result[k] = v.isoformat()
        elif isinstance(v, dict):
            result[k] = {kk: convert(vv) for kk, vv in v.items()}
        else:
            result[k] = v
    return result

if collection_choice == "audit_logs":
    docs = get_audit_logs(db)
elif collection_choice == "elections":
    docs = get_elections(db)[:20]
else:
    docs = get_alerts(db)[:20]

n_show = st.slider("Documents to show", 1, min(5, len(docs)), 2)

for doc in docs[:n_show]:
    clean = serialize_doc(doc)
    st.markdown(f'<div class="doc-card"><pre style="margin:0;white-space:pre-wrap;">{json.dumps(clean, indent=2)}</pre></div>', unsafe_allow_html=True)

# ─── Query showcase ───────────────────────────────────────────────────────────
st.markdown('<div class="section-head">Key MongoDB Queries — Bias Audit System</div>', unsafe_allow_html=True)

queries = [
    {
        "title": "1. Bias score trend across all Lok Sabha elections",
        "desc": "Core audit query — tracks fairness score improvement or deterioration over time.",
        "code": """db.audit_logs.find(
    {},
    {"election_year": 1, "bias_score": 1, "bias_flag": 1,
     "fairness_metrics.gender.win_rate_gap": 1}
).sort("election_year", 1)"""
    },
    {
        "title": "2. Worst states by gender win-rate gap",
        "desc": "Aggregation across all candidates — finds states where the gap is largest.",
        "code": """db.candidates.aggregate([
    {"$group": {
        "_id": "$state",
        "male_wins":    {"$sum": {"$cond": [{"$and": [{"$eq":["$gender","Male"]}, "$won"]}, 1, 0]}},
        "female_wins":  {"$sum": {"$cond": [{"$and": [{"$eq":["$gender","Female"]}, "$won"]}, 1, 0]}},
        "male_total":   {"$sum": {"$cond": [{"$eq":["$gender","Male"]}, 1, 0]}},
        "female_total": {"$sum": {"$cond": [{"$eq":["$gender","Female"]}, 1, 0]}},
    }},
    {"$project": {
        "win_rate_gap": {"$subtract": [
            {"$divide": ["$male_wins", {"$max":["$male_total",1]}]},
            {"$divide": ["$female_wins", {"$max":["$female_total",1]}]}
        ]}
    }},
    {"$sort": {"win_rate_gap": -1}}, {"$limit": 10}
])"""
    },
    {
        "title": "3. Average bias score per election (aggregation)",
        "desc": "Single-document aggregation showing average across all 6 elections.",
        "code": """db.audit_logs.aggregate([
    {"$group": {
        "_id": None,
        "avg_bias_score":     {"$avg": "$bias_score"},
        "avg_gender_bias":    {"$avg": "$component_scores.gender_bias"},
        "avg_caste_bias":     {"$avg": "$component_scores.caste_bias"},
        "avg_regional_bias":  {"$avg": "$component_scores.regional_bias"},
        "elections_flagged":  {"$sum": {"$cond": ["$bias_flag", 1, 0]}},
    }}
])"""
    },
    {
        "title": "4. All unresolved HIGH alerts (with threshold details)",
        "desc": "Monitoring query — used by the alerts panel for real-time status.",
        "code": """db.alerts.find(
    {"severity": "HIGH", "resolved": False},
    {"election_year": 1, "metric": 1, "threshold": 1,
     "actual_value": 1, "description": 1}
).sort("election_year", -1)"""
    },
    {
        "title": "5. Party-wise female candidate representation trend",
        "desc": "Flex schema in action — fairness_metrics.party_representation varies per document.",
        "code": """db.audit_logs.aggregate([
    {"$project": {
        "year": "$election_year",
        "bjp_female_share":  "$fairness_metrics.party_representation.BJP.female_share",
        "inc_female_share":  "$fairness_metrics.party_representation.INC.female_share",
        "tmc_female_share":  "$fairness_metrics.party_representation.TMC.female_share",
    }},
    {"$sort": {"year": 1}}
])"""
    },
]

for q in queries:
    st.markdown(f"""
    <div class="query-card">
        <div class="query-title">{q['title']}</div>
        <div class="query-desc">{q['desc']}</div>
    </div>""", unsafe_allow_html=True)
    st.code(q["code"], language="python")

# ─── Why MongoDB section ──────────────────────────────────────────────────────
st.markdown('<div class="section-head">Why MongoDB for This System?</div>', unsafe_allow_html=True)
st.markdown("""
**Flexible schema is the key advantage.** Each election's `audit_log` document has a different 
`fairness_metrics` shape — 1999 data doesn't have the same party breakdown as 2024. 
MongoDB handles this naturally; a SQL table would require `ALTER TABLE` or NULL-heavy rows.

The `fairness_metrics.party_representation` field is a perfect example: it contains only parties 
that contested in a given year. No rigid schema forces empty fields for parties that didn't exist yet.

Collections used: `elections`, `candidates`, `audit_logs`, `alerts`.
""")

st.markdown("---")
st.markdown(
    '<p style="font-family:IBM Plex Mono;font-size:0.72rem;color:#3A3A5C;text-align:center;">'
    'MongoDB Atlas · PyMongo 4.6 · Indian Election Bias Audit System</p>',
    unsafe_allow_html=True
)
