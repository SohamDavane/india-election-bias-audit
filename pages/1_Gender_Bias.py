"""
Page 2: Gender Bias Deep Dive
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from utils.db import get_database, get_audit_logs, get_state_bias

st.set_page_config(page_title="Gender Bias · India Election Audit", page_icon="♀", layout="wide")

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
state_data = get_state_bias(db)

st.markdown('<div class="page-title">♀ Gender Bias Analysis</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Win-rate gaps, candidate representation, and state-level disparities</div>', unsafe_allow_html=True)

years = [log["election_year"] for log in audit_logs]
male_win_rates = [log["fairness_metrics"]["gender"]["male_win_rate"] for log in audit_logs]
female_win_rates = [log["fairness_metrics"]["gender"]["female_win_rate"] for log in audit_logs]
female_shares = [log["fairness_metrics"]["gender"]["female_candidate_share"] for log in audit_logs]
female_counts = [log["fairness_metrics"]["gender"]["female_candidate_count"] for log in audit_logs]
male_counts = [log["fairness_metrics"]["gender"]["male_candidate_count"] for log in audit_logs]

# ─── Chart 1: Win rate comparison ────────────────────────────────────────────
st.markdown('<div class="section-head">Male vs Female Win Rate — All Elections</div>', unsafe_allow_html=True)

fig1 = go.Figure()
fig1.add_trace(go.Bar(x=years, y=male_win_rates, name="Male Win Rate",
                       marker_color="#4299E1", opacity=0.85,
                       text=[f"{v:.1%}" for v in male_win_rates],
                       textposition="outside", textfont=dict(family="IBM Plex Mono", size=10, color="#4299E1")))
fig1.add_trace(go.Bar(x=years, y=female_win_rates, name="Female Win Rate",
                       marker_color="#F687B3", opacity=0.85,
                       text=[f"{v:.1%}" for v in female_win_rates],
                       textposition="outside", textfont=dict(family="IBM Plex Mono", size=10, color="#F687B3")))

# Gap annotation
for i, (y, mw, fw) in enumerate(zip(years, male_win_rates, female_win_rates)):
    fig1.add_annotation(x=y, y=(mw + fw) / 2, text=f"gap {mw-fw:.0%}",
                         showarrow=False, font=dict(size=9, color="#FC8181", family="IBM Plex Mono"),
                         xshift=0)

fig1.update_layout(
    barmode="group", plot_bgcolor="#0D0D14", paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="IBM Plex Mono", size=11, color="#6B6B9A"),
    legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=-0.15),
    margin=dict(l=10, r=10, t=20, b=10),
    xaxis=dict(gridcolor="#1E1E35", tickmode="array", tickvals=years),
    yaxis=dict(gridcolor="#1E1E35", tickformat=".0%"),
)
st.plotly_chart(fig1, use_container_width=True)

# ─── Chart 2: Candidate composition ──────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="section-head">Candidate Composition by Gender</div>', unsafe_allow_html=True)
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=years, y=male_counts, name="Male Candidates",
                           marker_color="#2B4C7E", opacity=0.9))
    fig2.add_trace(go.Bar(x=years, y=female_counts, name="Female Candidates",
                           marker_color="#F687B3", opacity=0.9,
                           text=[f"{s:.0%}" for s in female_shares],
                           textposition="outside",
                           textfont=dict(family="IBM Plex Mono", size=10, color="#F687B3")))
    fig2.add_hline(y=0, line_color="#1E1E35")
    fig2.update_layout(
        barmode="stack", plot_bgcolor="#0D0D14", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Mono", size=11, color="#6B6B9A"),
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=-0.18),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(gridcolor="#1E1E35", tickmode="array", tickvals=years),
        yaxis=dict(gridcolor="#1E1E35"),
    )
    st.plotly_chart(fig2, use_container_width=True)

with col2:
    st.markdown('<div class="section-head">Female Candidate Share Trend</div>', unsafe_allow_html=True)
    fig3 = go.Figure()
    fig3.add_hrect(y0=0.33, y1=0.40, fillcolor="rgba(104,211,145,0.07)",
                   annotation_text="33% reservation target", line_width=0,
                   annotation_font=dict(size=9, color="#68D391"))
    fig3.add_trace(go.Scatter(
        x=years, y=female_shares, mode="lines+markers+text",
        line=dict(color="#F687B3", width=3),
        marker=dict(size=10, color="#F687B3", line=dict(color="#08080F", width=2)),
        text=[f"{v:.1%}" for v in female_shares],
        textposition="top center",
        textfont=dict(family="IBM Plex Mono", size=10, color="#F687B3"),
        fill="tozeroy", fillcolor="rgba(246,135,179,0.07)",
    ))
    fig3.update_layout(
        plot_bgcolor="#0D0D14", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Mono", size=11, color="#6B6B9A"),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(gridcolor="#1E1E35", tickmode="array", tickvals=years),
        yaxis=dict(gridcolor="#1E1E35", tickformat=".0%"),
        showlegend=False,
    )
    st.plotly_chart(fig3, use_container_width=True)

# ─── State-level table ────────────────────────────────────────────────────────
st.markdown('<div class="section-head">State-Level Gender Win-Rate Gap (All Elections Combined)</div>', unsafe_allow_html=True)

df_state = pd.DataFrame(state_data)
df_state = df_state[["state", "female_share", "male_win_rate", "female_win_rate", "win_rate_gap"]].copy()
df_state.columns = ["State", "Female Candidate Share", "Male Win Rate", "Female Win Rate", "Win Rate Gap"]
df_state["Female Candidate Share"] = df_state["Female Candidate Share"].map("{:.1%}".format)
df_state["Male Win Rate"] = df_state["Male Win Rate"].map("{:.1%}".format)
df_state["Female Win Rate"] = df_state["Female Win Rate"].map("{:.1%}".format)
df_state["Win Rate Gap ▼"] = df_state["Win Rate Gap"].map("{:.1%}".format)
df_state = df_state.drop(columns=["Win Rate Gap"])

st.dataframe(df_state.head(20), use_container_width=True, hide_index=True)

# ─── MongoDB query ────────────────────────────────────────────────────────────
st.markdown('<div class="section-head">MongoDB Query — State Gender Gap Aggregation</div>', unsafe_allow_html=True)
with st.expander("View query"):
    st.code("""
db.candidates.aggregate([
    {"$group": {
        "_id": "$state",
        "male_wins":   {"$sum": {"$cond": [{"$and": [{"$eq":["$gender","Male"]},   "$won"]}, 1, 0]}},
        "female_wins": {"$sum": {"$cond": [{"$and": [{"$eq":["$gender","Female"]}, "$won"]}, 1, 0]}},
        "male_total":   {"$sum": {"$cond": [{"$eq": ["$gender", "Male"]},   1, 0]}},
        "female_total": {"$sum": {"$cond": [{"$eq": ["$gender", "Female"]}, 1, 0]}},
    }},
    {"$project": {
        "state": "$_id",
        "male_win_rate":   {"$divide": ["$male_wins",   {"$max": ["$male_total",   1]}]},
        "female_win_rate": {"$divide": ["$female_wins", {"$max": ["$female_total", 1]}]},
    }},
    {"$addFields": {
        "win_rate_gap": {"$subtract": ["$male_win_rate", "$female_win_rate"]}
    }},
    {"$sort": {"win_rate_gap": -1}}
])
""", language="python")
