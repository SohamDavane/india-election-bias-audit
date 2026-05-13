"""
Page 7: Constituency & State Drill-Down Explorer
Deep dive into individual states — candidate profiles, win rates, gender gaps.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import random
from utils.db import get_database
from utils.data_generator import STATES, PARTIES, CASTE_CATEGORIES, ELECTIONS, get_region

st.set_page_config(page_title="Drill-Down · India Election Audit", page_icon="🔍", layout="wide")

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
.stat-pill {
    display: inline-block; padding: 0.4rem 1rem; border-radius: 6px;
    font-family: 'IBM Plex Mono', monospace; font-size: 0.85rem;
    background: #0D0D14; border: 1px solid #1E1E35; color: #C8C8E0;
    margin: 0.2rem;
}
.stat-val { font-weight: 700; color: #F0F0FF; }
.candidate-row {
    display: flex; align-items: center; gap: 0.8rem; padding: 0.6rem 0.8rem;
    background: #0A0A12; border: 1px solid #1A1A28; border-radius: 6px;
    margin-bottom: 0.4rem; font-size: 0.82rem; color: #C8C8E0;
}
.won-badge { padding: 0.1rem 0.5rem; border-radius: 3px; font-family: 'IBM Plex Mono', monospace;
             font-size: 0.68rem; background: rgba(104,211,145,0.12); color: #68D391;
             border: 1px solid rgba(104,211,145,0.25); }
.lost-badge { padding: 0.1rem 0.5rem; border-radius: 3px; font-family: 'IBM Plex Mono', monospace;
              font-size: 0.68rem; background: rgba(107,107,154,0.08); color: #6B6B9A;
              border: 1px solid #1E1E35; }
.female-tag { color: #F687B3; font-size: 0.75rem; }
.male-tag { color: #4299E1; font-size: 0.75rem; }
</style>
""", unsafe_allow_html=True)

# ─── Seed state candidate data (cached) ───────────────────────────────────────
@st.cache_data(show_spinner=False)
def get_state_candidates():
    """Generate per-state candidate data across all elections."""
    random.seed(42)
    from utils.data_generator import (
        FEMALE_CANDIDATE_SHARE, FEMALE_WIN_RATE, MALE_WIN_RATE,
        GENERAL_WIN_RATE_MULTIPLIER, OBC_WIN_RATE_MULTIPLIER,
        SC_WIN_RATE_MULTIPLIER, ST_WIN_RATE_MULTIPLIER
    )
    caste_mult = {
        "General": GENERAL_WIN_RATE_MULTIPLIER, "OBC": OBC_WIN_RATE_MULTIPLIER,
        "SC": SC_WIN_RATE_MULTIPLIER, "ST": ST_WIN_RATE_MULTIPLIER
    }
    
    NAME_POOL_M = [
        "Rajesh Kumar", "Suresh Singh", "Arun Sharma", "Vikram Yadav", "Mahesh Gupta",
        "Ravi Patel", "Dinesh Tiwari", "Prakash Joshi", "Sanjay Mishra", "Amit Verma",
        "Rahul Gandhi", "Narendra Patel", "Arvind Kumar", "Gopal Das", "Hemant Rao",
        "Kamlesh Bajpai", "Lalit Mohan", "Mukesh Aggarwal", "Nitin Desai", "Omkar Nath"
    ]
    NAME_POOL_F = [
        "Priya Sharma", "Sunita Devi", "Rekha Singh", "Meena Kumari", "Anita Yadav",
        "Kavita Gupta", "Lata Mishra", "Nirmala Joshi", "Savita Verma", "Uma Rani",
        "Smriti Irani", "Hema Malini", "Kiran Bedi", "Mamata Devi", "Sushma Verma",
        "Geeta Patel", "Asha Kumari", "Bhavna Rao", "Chandrika Singh", "Devyani Shah"
    ]
    
    docs = []
    for state in STATES:
        for e in ELECTIONS:
            year = e["year"]
            n_cands = random.randint(15, 60)
            female_share = FEMALE_CANDIDATE_SHARE[year]
            
            for i in range(n_cands):
                is_female = random.random() < female_share
                gender = "Female" if is_female else "Male"
                caste = random.choices(CASTE_CATEGORIES, weights=[30, 40, 20, 10])[0]
                party = random.choice(PARTIES)
                
                base_win = FEMALE_WIN_RATE[year] if is_female else MALE_WIN_RATE[year]
                win_prob = min(base_win * caste_mult[caste] * random.uniform(0.7, 1.3), 0.95)
                won = random.random() < (win_prob * 0.15)
                
                name = random.choice(NAME_POOL_F if is_female else NAME_POOL_M)
                
                docs.append({
                    "state": state,
                    "election_year": year,
                    "name": name,
                    "party": party,
                    "gender": gender,
                    "caste_category": caste,
                    "votes": random.randint(8000, 750000),
                    "won": won,
                    "region": get_region(state),
                })
    return pd.DataFrame(docs)

db, _ = get_database()
df_all = get_state_candidates()

st.markdown('<div class="page-title">🔍 Constituency Drill-Down</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Explore any state and election year — candidate profiles, bias scores, party breakdown</div>', unsafe_allow_html=True)

# ─── Filters ──────────────────────────────────────────────────────────────────
col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
with col_f1:
    selected_state = st.selectbox("Select State", sorted(STATES))
with col_f2:
    selected_year = st.selectbox("Election Year", [e["year"] for e in ELECTIONS], index=4)
with col_f3:
    gender_filter = st.selectbox("Gender Filter", ["All", "Female", "Male"])

# Filter data
df = df_all[(df_all["state"] == selected_state) & (df_all["election_year"] == selected_year)].copy()
if gender_filter != "All":
    df_view = df[df["gender"] == gender_filter]
else:
    df_view = df

# ─── State summary stats ──────────────────────────────────────────────────────
total = len(df)
female_c = (df["gender"] == "Female").sum()
male_c = (df["gender"] == "Male").sum()
female_share = female_c / max(total, 1)
winners = df["won"].sum()
female_wins = df[df["gender"] == "Female"]["won"].sum()
male_wins = df[df["gender"] == "Male"]["won"].sum()
female_wr = female_wins / max(female_c, 1)
male_wr = male_wins / max(male_c, 1)
wr_gap = male_wr - female_wr

region = get_region(selected_state)
bias_flag = wr_gap > 0.30 or female_share < 0.10

st.markdown(f"""
<div style="background:#0D0D14;border:1px solid {'#E53E3E' if bias_flag else '#138808'};
            border-radius:10px;padding:1.2rem 1.4rem;margin-bottom:1rem;">
    <div style="display:flex;align-items:center;gap:0.8rem;margin-bottom:0.8rem;">
        <span style="font-size:1.2rem;font-weight:800;color:#F0F0FF;">{selected_state}</span>
        <span style="font-family:'IBM Plex Mono',monospace;font-size:0.72rem;color:#6B6B9A;">
            {region} region · Lok Sabha {selected_year}
        </span>
        <span style="margin-left:auto;padding:0.2rem 0.8rem;border-radius:4px;font-family:'IBM Plex Mono',monospace;
                     font-size:0.72rem;background:{'rgba(229,62,62,0.12)' if bias_flag else 'rgba(19,136,8,0.12)'};
                     color:{'#FC8181' if bias_flag else '#68D391'};
                     border:1px solid {'rgba(229,62,62,0.3)' if bias_flag else 'rgba(19,136,8,0.3)'};">
            {'⚠ BIAS FLAGGED' if bias_flag else '✓ WITHIN THRESHOLD'}
        </span>
    </div>
    <div>
        <span class="stat-pill">Candidates: <span class="stat-val">{total}</span></span>
        <span class="stat-pill">Female: <span class="stat-val" style="color:#F687B3;">{female_c} ({female_share:.0%})</span></span>
        <span class="stat-pill">Male: <span class="stat-val" style="color:#4299E1;">{male_c}</span></span>
        <span class="stat-pill">Winners: <span class="stat-val" style="color:#68D391;">{winners}</span></span>
        <span class="stat-pill">Female win rate: <span class="stat-val" style="color:#F687B3;">{female_wr:.1%}</span></span>
        <span class="stat-pill">Male win rate: <span class="stat-val" style="color:#4299E1;">{male_wr:.1%}</span></span>
        <span class="stat-pill">Win gap: <span class="stat-val" style="color:{'#FC8181' if wr_gap > 0.3 else '#F6AD55'};">{wr_gap:.1%}</span></span>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── Charts ───────────────────────────────────────────────────────────────────
col_l, col_r = st.columns(2)

with col_l:
    st.markdown('<div class="section-head">Party Breakdown — Candidates & Winners</div>', unsafe_allow_html=True)
    party_grp = df.groupby("party").agg(
        total=("gender", "count"),
        female=("gender", lambda x: (x == "Female").sum()),
        winners=("won", "sum")
    ).reset_index().sort_values("total", ascending=False).head(8)
    
    fig_p = go.Figure()
    fig_p.add_trace(go.Bar(name="Total", x=party_grp["party"].tolist(), y=party_grp["total"].tolist(),
                            marker_color="#2B4C7E", opacity=0.7))
    fig_p.add_trace(go.Bar(name="Female", x=party_grp["party"].tolist(), y=party_grp["female"].tolist(),
                            marker_color="#F687B3", opacity=0.9))
    fig_p.add_trace(go.Bar(name="Winners", x=party_grp["party"].tolist(), y=party_grp["winners"].tolist(),
                            marker_color="#68D391", opacity=0.9))
    fig_p.update_layout(
        barmode="group", plot_bgcolor="#0D0D14", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Mono", size=10, color="#6B6B9A"),
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=-0.2),
        margin=dict(l=5, r=5, t=5, b=5),
        xaxis=dict(gridcolor="#1E1E35", tickangle=-30),
        yaxis=dict(gridcolor="#1E1E35"),
    )
    st.plotly_chart(fig_p, use_container_width=True)

with col_r:
    st.markdown('<div class="section-head">Caste Category Distribution</div>', unsafe_allow_html=True)
    caste_grp = df.groupby("caste_category").agg(
        total=("gender", "count"),
        wins=("won", "sum")
    ).reset_index()
    caste_grp["win_rate"] = caste_grp["wins"] / caste_grp["total"]
    
    caste_colors_map = {"General": "#4299E1", "OBC": "#FF9933", "SC": "#F687B3", "ST": "#68D391"}
    
    fig_c = go.Figure()
    fig_c.add_trace(go.Bar(
        x=caste_grp["caste_category"].tolist(),
        y=caste_grp["win_rate"].tolist(),
        marker=dict(color=[caste_colors_map.get(c, "#888") for c in caste_grp["caste_category"].tolist()]),
        text=[f"{v:.1%}" for v in caste_grp["win_rate"].tolist()],
        textposition="outside",
        textfont=dict(family="IBM Plex Mono", size=11, color="#C8C8E0"),
    ))
    fig_c.update_layout(
        plot_bgcolor="#0D0D14", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Mono", size=11, color="#6B6B9A"),
        margin=dict(l=5, r=5, t=5, b=5),
        xaxis=dict(gridcolor="#1E1E35"),
        yaxis=dict(gridcolor="#1E1E35", tickformat=".0%", title="Win Rate"),
        showlegend=False,
    )
    st.plotly_chart(fig_c, use_container_width=True)

# ─── State trend over all elections ───────────────────────────────────────────
st.markdown(f'<div class="section-head">Gender Win-Rate Gap Trend — {selected_state} (1999–2024)</div>', unsafe_allow_html=True)

state_trend = []
for e in ELECTIONS:
    yr = e["year"]
    df_yr = df_all[(df_all["state"] == selected_state) & (df_all["election_year"] == yr)]
    f_wr = df_yr[df_yr["gender"] == "Female"]["won"].mean() if len(df_yr[df_yr["gender"] == "Female"]) > 0 else 0
    m_wr = df_yr[df_yr["gender"] == "Male"]["won"].mean() if len(df_yr[df_yr["gender"] == "Male"]) > 0 else 0
    f_sh = (df_yr["gender"] == "Female").sum() / max(len(df_yr), 1)
    state_trend.append({"year": yr, "female_wr": f_wr, "male_wr": m_wr, "gap": m_wr - f_wr, "female_share": f_sh})

df_trend = pd.DataFrame(state_trend)
fig_t = go.Figure()
fig_t.add_trace(go.Scatter(x=df_trend["year"].tolist(), y=df_trend["male_wr"].tolist(),
                            name="Male Win Rate", mode="lines+markers",
                            line=dict(color="#4299E1", width=2.5),
                            marker=dict(size=8, color="#4299E1")))
fig_t.add_trace(go.Scatter(x=df_trend["year"].tolist(), y=df_trend["female_wr"].tolist(),
                            name="Female Win Rate", mode="lines+markers",
                            line=dict(color="#F687B3", width=2.5),
                            marker=dict(size=8, color="#F687B3")))
fig_t.add_trace(go.Scatter(x=df_trend["year"].tolist(), y=df_trend["gap"].tolist(),
                            name="Gap", mode="lines+markers",
                            line=dict(color="#FC8181", width=2, dash="dash"),
                            marker=dict(size=7)))
fig_t.add_hline(y=0.30, line_dash="dot", line_color="#6B6B9A",
                annotation_text="bias threshold", annotation_font=dict(size=9, color="#6B6B9A"))
fig_t.update_layout(
    plot_bgcolor="#0D0D14", paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="IBM Plex Mono", size=11, color="#6B6B9A"),
    legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=-0.15),
    margin=dict(l=10, r=10, t=10, b=10),
    xaxis=dict(gridcolor="#1E1E35", tickmode="array", tickvals=[e["year"] for e in ELECTIONS]),
    yaxis=dict(gridcolor="#1E1E35", tickformat=".0%"),
    hovermode="x unified",
)
st.plotly_chart(fig_t, use_container_width=True)

# ─── Candidate list ───────────────────────────────────────────────────────────
st.markdown(f'<div class="section-head">Candidate Records — {selected_state} · {selected_year} ({len(df_view)} shown)</div>', unsafe_allow_html=True)

df_sorted = df_view.sort_values(["won", "votes"], ascending=[False, False]).head(25)
for _, row in df_sorted.iterrows():
    gender_cls = "female-tag" if row["gender"] == "Female" else "male-tag"
    gender_sym = "♀" if row["gender"] == "Female" else "♂"
    badge = '<span class="won-badge">WON</span>' if row["won"] else '<span class="lost-badge">lost</span>'
    
    st.markdown(f"""
    <div class="candidate-row">
        {badge}
        <span style="font-weight:600;min-width:150px;">{row['name']}</span>
        <span class="{gender_cls}">{gender_sym} {row['gender']}</span>
        <span style="color:#6B6B9A;font-size:0.78rem;font-family:'IBM Plex Mono',monospace;">
            {row['party']}
        </span>
        <span style="color:#8888AA;font-size:0.75rem;font-family:'IBM Plex Mono',monospace;">
            {row['caste_category']}
        </span>
        <span style="margin-left:auto;font-family:'IBM Plex Mono',monospace;font-size:0.80rem;color:#9090B8;">
            {row['votes']:,} votes
        </span>
    </div>
    """, unsafe_allow_html=True)

# ─── MongoDB query ────────────────────────────────────────────────────────────
st.markdown('<div class="section-head">MongoDB Query — State Drill-Down</div>', unsafe_allow_html=True)
with st.expander("View query"):
    st.code(f"""
# Drill down into a specific state and election year
db.candidates.find({{
    "state": "{selected_state}",
    "election_year": {selected_year}
}}).sort([("won", -1), ("votes", -1)])

# State-level gender bias summary
db.candidates.aggregate([
    {{"$match": {{"state": "{selected_state}"}}}},
    {{"$group": {{
        "_id": {{"year": "$election_year", "gender": "$gender"}},
        "total": {{"$sum": 1}},
        "wins":  {{"$sum": {{"$cond": ["$won", 1, 0]}}}}
    }}}},
    {{"$project": {{
        "year": "$_id.year",
        "gender": "$_id.gender",
        "win_rate": {{"$divide": ["$wins", {{"$max": ["$total", 1]}}]}}
    }}}},
    {{"$sort": {{"year": 1, "gender": 1}}}}
])
""", language="python")
