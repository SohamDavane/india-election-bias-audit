"""
Page 4: Caste & Regional Bias
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.db import get_database, get_audit_logs

st.set_page_config(page_title="Caste & Regional Bias · India Election Audit", page_icon="🗺", layout="wide")

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
</style>
""", unsafe_allow_html=True)

db, _ = get_database()
audit_logs = get_audit_logs(db)

st.markdown('<div class="page-title">🗺 Caste & Regional Bias</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Win-rate disparity across caste categories and voter turnout by region</div>', unsafe_allow_html=True)

years = [log["election_year"] for log in audit_logs]
caste_cats = ["General", "OBC", "SC", "ST"]
caste_colors = {"General": "#4299E1", "OBC": "#FF9933", "SC": "#F687B3", "ST": "#68D391"}

# ─── Caste win rates over time ────────────────────────────────────────────────
st.markdown('<div class="section-head">Caste Category Win Rates — Trend Over Elections</div>', unsafe_allow_html=True)

fig1 = go.Figure()
for cat in caste_cats:
    rates = [log["fairness_metrics"]["caste"]["win_rates_by_category"].get(cat, 0) for log in audit_logs]
    fig1.add_trace(go.Scatter(
        x=years, y=rates, mode="lines+markers",
        name=cat, line=dict(color=caste_colors[cat], width=2.5),
        marker=dict(size=8, color=caste_colors[cat], line=dict(color="#08080F", width=1.5)),
    ))

fig1.update_layout(
    plot_bgcolor="#0D0D14", paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="IBM Plex Mono", size=11, color="#6B6B9A"),
    legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=-0.15),
    margin=dict(l=10, r=10, t=10, b=10),
    xaxis=dict(gridcolor="#1E1E35", tickmode="array", tickvals=years),
    yaxis=dict(gridcolor="#1E1E35", tickformat=".1%", title="Win Rate"),
    hovermode="x unified",
)
st.plotly_chart(fig1, use_container_width=True)

# ─── Caste gap ────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="section-head">Max Caste Win-Rate Gap Per Election</div>', unsafe_allow_html=True)
    max_gaps = [log["fairness_metrics"]["caste"]["max_gap"] for log in audit_logs]
    
    fig2 = go.Figure(go.Bar(
        x=years, y=max_gaps,
        marker=dict(color=["#E53E3E" if g > 0.06 else "#F6AD55" for g in max_gaps]),
        text=[f"{g:.1%}" for g in max_gaps],
        textposition="outside",
        textfont=dict(family="IBM Plex Mono", size=10, color="#C8C8E0"),
    ))
    fig2.add_hline(y=0.06, line_dash="dot", line_color="#6B6B9A",
                   annotation_text="threshold 6%", annotation_font=dict(size=9, color="#6B6B9A"))
    fig2.update_layout(
        plot_bgcolor="#0D0D14", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Mono", size=11, color="#6B6B9A"),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(gridcolor="#1E1E35", tickmode="array", tickvals=years),
        yaxis=dict(gridcolor="#1E1E35", tickformat=".1%"),
        showlegend=False,
    )
    st.plotly_chart(fig2, use_container_width=True)

with col2:
    st.markdown('<div class="section-head">Caste Win Rate Breakdown — 2024</div>', unsafe_allow_html=True)
    latest = audit_logs[-1]
    caste_rates = latest["fairness_metrics"]["caste"]["win_rates_by_category"]
    
    fig3 = go.Figure(go.Bar(
        x=list(caste_rates.keys()),
        y=list(caste_rates.values()),
        marker=dict(color=[caste_colors.get(k, "#888") for k in caste_rates.keys()]),
        text=[f"{v:.1%}" for v in caste_rates.values()],
        textposition="outside",
        textfont=dict(family="IBM Plex Mono", size=11, color="#C8C8E0"),
    ))
    fig3.update_layout(
        plot_bgcolor="#0D0D14", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Mono", size=11, color="#6B6B9A"),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(gridcolor="#1E1E35"),
        yaxis=dict(gridcolor="#1E1E35", tickformat=".1%"),
        showlegend=False,
    )
    st.plotly_chart(fig3, use_container_width=True)

# ─── Regional turnout ─────────────────────────────────────────────────────────
st.markdown('<div class="section-head">Regional Voter Turnout Trend — North vs South Gap</div>', unsafe_allow_html=True)

regions = {
    "North": [log["fairness_metrics"]["regional"]["north_turnout"] for log in audit_logs],
    "South": [log["fairness_metrics"]["regional"]["south_turnout"] for log in audit_logs],
    "East":  [log["fairness_metrics"]["regional"]["east_turnout"] for log in audit_logs],
    "West":  [log["fairness_metrics"]["regional"]["west_turnout"] for log in audit_logs],
    "NE":    [log["fairness_metrics"]["regional"]["ne_turnout"] for log in audit_logs],
}
region_colors = {"North": "#4299E1", "South": "#68D391", "East": "#F6AD55", "West": "#F687B3", "NE": "#9F7AEA"}

fig4 = go.Figure()
for region, vals in regions.items():
    fig4.add_trace(go.Scatter(
        x=years, y=vals, mode="lines+markers",
        name=region, line=dict(color=region_colors[region], width=2),
        marker=dict(size=7, color=region_colors[region]),
    ))

fig4.update_layout(
    plot_bgcolor="#0D0D14", paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="IBM Plex Mono", size=11, color="#6B6B9A"),
    legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=-0.15),
    margin=dict(l=10, r=10, t=10, b=10),
    xaxis=dict(gridcolor="#1E1E35", tickmode="array", tickvals=years),
    yaxis=dict(gridcolor="#1E1E35", tickformat=".0%", title="Voter Turnout"),
    hovermode="x unified",
)
st.plotly_chart(fig4, use_container_width=True)

# ─── North-South gap ─────────────────────────────────────────────────────────
st.markdown('<div class="section-head">North–South Turnout Gap (Largest Persistent Disparity)</div>', unsafe_allow_html=True)
gaps = [log["fairness_metrics"]["regional"]["north_south_gap"] for log in audit_logs]

fig5 = go.Figure()
fig5.add_trace(go.Scatter(
    x=years, y=gaps, mode="lines+markers+text",
    line=dict(color="#9F7AEA", width=3),
    marker=dict(size=10, color="#9F7AEA", line=dict(color="#08080F", width=2)),
    text=[f"{g:.1%}" for g in gaps],
    textposition="top center",
    textfont=dict(family="IBM Plex Mono", size=10, color="#9F7AEA"),
    fill="tozeroy", fillcolor="rgba(159,122,234,0.07)",
))
fig5.add_hline(y=0.08, line_dash="dot", line_color="#FC8181",
               annotation_text="alert threshold 8%", annotation_font=dict(size=9, color="#FC8181"))
fig5.update_layout(
    plot_bgcolor="#0D0D14", paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="IBM Plex Mono", size=11, color="#6B6B9A"),
    margin=dict(l=10, r=10, t=10, b=10),
    xaxis=dict(gridcolor="#1E1E35", tickmode="array", tickvals=years),
    yaxis=dict(gridcolor="#1E1E35", tickformat=".1%"),
    showlegend=False,
)
st.plotly_chart(fig5, use_container_width=True)

# ─── MongoDB query ────────────────────────────────────────────────────────────
st.markdown('<div class="section-head">MongoDB Query — Caste Win Rate Aggregation</div>', unsafe_allow_html=True)
with st.expander("View query"):
    st.code("""
# Caste win rates per election
db.candidates.aggregate([
    {"$group": {
        "_id": {"caste": "$caste_category", "year": "$election_year"},
        "total": {"$sum": 1},
        "wins":  {"$sum": {"$cond": ["$won", 1, 0]}},
    }},
    {"$project": {
        "caste": "$_id.caste",
        "year": "$_id.year",
        "win_rate": {"$divide": ["$wins", "$total"]},
    }},
    {"$sort": {"year": 1, "caste": 1}}
])
""", language="python")
