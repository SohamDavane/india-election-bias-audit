"""
Page 3: Party Fairness Scorecard
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.db import get_database, get_party_metrics, get_audit_logs

st.set_page_config(page_title="Party Scorecard · India Election Audit", page_icon="🏛", layout="wide")

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
.scorecard {
    background: #0D0D14; border: 1px solid #1E1E35; border-radius: 10px;
    padding: 1.2rem; margin-bottom: 0.8rem;
}
.party-name { font-size: 1.3rem; font-weight: 700; color: #F0F0FF; }
.party-score { font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; color: #6B6B9A; }
.grade-A { color: #68D391; font-size: 2rem; font-weight: 800; }
.grade-B { color: #F6AD55; font-size: 2rem; font-weight: 800; }
.grade-C { color: #FC8181; font-size: 2rem; font-weight: 800; }
</style>
""", unsafe_allow_html=True)

db, _ = get_database()
party_rows = get_party_metrics(db)
audit_logs = get_audit_logs(db)

st.markdown('<div class="page-title">🏛 Party Fairness Scorecard</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Which parties actually field women? Candidate share vs win rate</div>', unsafe_allow_html=True)

PARTIES = ["BJP", "INC", "TMC", "SP", "BSP"]
PARTY_COLORS = {"BJP": "#FF9933", "INC": "#138808", "TMC": "#1A5276", "SP": "#C0392B", "BSP": "#3498DB"}

# Build summary per party across all years
df = pd.DataFrame(party_rows)
if "party" not in df.columns:
    st.error("No party data available.")
    st.stop()

df_summary = df.groupby("party").agg(
    total_candidates=("total", "sum"),
    total_female=("female", "sum"),
    avg_female_share=("female_share", "mean"),
    avg_win_rate=("win_rate", "mean"),
).reset_index()
df_summary["grade"] = df_summary["avg_female_share"].apply(
    lambda x: "A" if x >= 0.20 else ("B" if x >= 0.12 else "C")
)
df_summary = df_summary.sort_values("avg_female_share", ascending=False)

# ─── Scorecard cards ──────────────────────────────────────────────────────────
st.markdown('<div class="section-head">2024 Fairness Grades</div>', unsafe_allow_html=True)

cols = st.columns(len(PARTIES))
for i, row in enumerate(df_summary.itertuples()):
    if row.party not in PARTIES:
        continue
    grade_cls = f"grade-{row.grade}"
    color = PARTY_COLORS.get(row.party, "#888")
    with cols[i % len(cols)]:
        st.markdown(f"""
        <div class="scorecard" style="border-left: 3px solid {color};">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div class="party-name">{row.party}</div>
                <div class="{grade_cls}">{row.grade}</div>
            </div>
            <div class="party-score">Female share: {row.avg_female_share:.1%}</div>
            <div class="party-score">Avg win rate: {row.avg_win_rate:.1%}</div>
            <div class="party-score">Total candidates: {int(row.total_candidates):,}</div>
        </div>
        """, unsafe_allow_html=True)

# ─── Female share trend by party ──────────────────────────────────────────────
st.markdown('<div class="section-head">Female Candidate Share by Party — 1999 to 2024</div>', unsafe_allow_html=True)

fig = go.Figure()
for party in PARTIES:
    p_data = df[df["party"] == party].sort_values("year")
    if p_data.empty:
        continue
    color = PARTY_COLORS.get(party, "#888")
    fig.add_trace(go.Scatter(
        x=p_data["year"].tolist(), y=p_data["female_share"].tolist(),
        mode="lines+markers", name=party,
        line=dict(color=color, width=2.5),
        marker=dict(size=8, color=color, line=dict(color="#08080F", width=1.5)),
    ))

fig.add_hline(y=0.33, line_dash="dot", line_color="#6B6B9A",
              annotation_text="33% target", annotation_font=dict(size=9, color="#6B6B9A"))

fig.update_layout(
    plot_bgcolor="#0D0D14", paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="IBM Plex Mono", size=11, color="#6B6B9A"),
    legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=-0.15),
    margin=dict(l=10, r=10, t=10, b=10),
    xaxis=dict(gridcolor="#1E1E35", tickmode="array",
               tickvals=[1999, 2004, 2009, 2014, 2019, 2024]),
    yaxis=dict(gridcolor="#1E1E35", tickformat=".0%"),
    hovermode="x unified",
)
st.plotly_chart(fig, use_container_width=True)

# ─── Bubble chart: female share vs win rate ───────────────────────────────────
st.markdown('<div class="section-head">Female Candidate Share vs Win Rate (2024)</div>', unsafe_allow_html=True)

latest_year = df["year"].max()
df_latest = df[df["year"] == latest_year]

fig2 = go.Figure()
for _, row in df_latest.iterrows():
    color = PARTY_COLORS.get(row["party"], "#888")
    fig2.add_trace(go.Scatter(
        x=[row["female_share"]], y=[row["win_rate"]],
        mode="markers+text",
        marker=dict(size=row["total"] / 30, color=color, opacity=0.75,
                    line=dict(color="#08080F", width=1)),
        text=[row["party"]],
        textposition="top center",
        textfont=dict(family="IBM Plex Mono", size=10, color=color),
        name=row["party"],
        showlegend=False,
    ))

fig2.add_vline(x=0.33, line_dash="dot", line_color="#6B6B9A",
               annotation_text="33% target", annotation_font=dict(size=9, color="#6B6B9A"))

fig2.update_layout(
    plot_bgcolor="#0D0D14", paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="IBM Plex Mono", size=11, color="#6B6B9A"),
    margin=dict(l=10, r=10, t=10, b=10),
    xaxis=dict(gridcolor="#1E1E35", tickformat=".0%", title="Female Candidate Share"),
    yaxis=dict(gridcolor="#1E1E35", tickformat=".0%", title="Overall Win Rate"),
)
st.plotly_chart(fig2, use_container_width=True)

# ─── MongoDB query ────────────────────────────────────────────────────────────
st.markdown('<div class="section-head">MongoDB Aggregation — Party Female Share</div>', unsafe_allow_html=True)
with st.expander("View query"):
    st.code("""
db.candidates.aggregate([
    {"$group": {
        "_id": {"party": "$party", "year": "$election_year"},
        "total":          {"$sum": 1},
        "female":         {"$sum": {"$cond": [{"$eq": ["$gender", "Female"]}, 1, 0]}},
        "female_winners": {"$sum": {"$cond": [
            {"$and": [{"$eq": ["$gender", "Female"]}, "$won"]}, 1, 0
        ]}},
    }},
    {"$project": {
        "party": "$_id.party",
        "year": "$_id.year",
        "female_share": {"$divide": ["$female", "$total"]},
        "female_win_rate": {"$divide": [
            "$female_winners",
            {"$max": ["$female", 1]}
        ]},
    }},
    {"$sort": {"year": 1, "female_share": -1}}
])
""", language="python")
