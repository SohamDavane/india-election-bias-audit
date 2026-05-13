"""
🗳️ Indian Election Bias Audit System
Main dashboard — Overview & Bias Score Trends
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from utils.db import get_database, seed_database, get_audit_logs, get_alerts

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="India Election Bias Audit",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=IBM+Plex+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #0D0D14;
    border-right: 1px solid #1E1E2E;
}
section[data-testid="stSidebar"] * {
    color: #C8C8E0 !important;
}

/* Header */
.main-header {
    background: linear-gradient(135deg, #0D0D14 0%, #12122A 50%, #0D0D14 100%);
    border: 1px solid #1E1E35;
    border-radius: 12px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.main-header::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -10%;
    width: 400px;
    height: 400px;
    background: radial-gradient(circle, rgba(255,153,51,0.08) 0%, transparent 70%);
    pointer-events: none;
}
.main-header::after {
    content: '';
    position: absolute;
    bottom: -40%;
    left: 20%;
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, rgba(19,136,8,0.06) 0%, transparent 70%);
    pointer-events: none;
}
.header-title {
    font-size: 2.4rem;
    font-weight: 800;
    color: #F0F0FF;
    letter-spacing: -0.5px;
    margin-bottom: 0.3rem;
}
.header-title span.india {
    background: linear-gradient(90deg, #FF9933 33%, #FFFFFF 33%, #FFFFFF 66%, #138808 66%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.header-sub {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    color: #6B6B9A;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

/* Metric cards */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin-bottom: 1.5rem;
}
.metric-card {
    background: #0D0D14;
    border: 1px solid #1E1E35;
    border-radius: 10px;
    padding: 1.2rem 1.4rem;
    position: relative;
    overflow: hidden;
}
.metric-card.danger { border-left: 3px solid #E53E3E; }
.metric-card.warning { border-left: 3px solid #FF9933; }
.metric-card.info { border-left: 3px solid #138808; }
.metric-card.neutral { border-left: 3px solid #6B6B9A; }
.metric-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    color: #6B6B9A;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.4rem;
}
.metric-value {
    font-size: 2rem;
    font-weight: 800;
    color: #F0F0FF;
    line-height: 1;
}
.metric-delta {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    margin-top: 0.3rem;
}
.delta-up { color: #68D391; }
.delta-down { color: #E53E3E; }

/* Alert badge */
.alert-badge {
    display: inline-block;
    padding: 0.15rem 0.6rem;
    border-radius: 4px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    font-weight: 500;
}
.badge-high { background: rgba(229,62,62,0.15); color: #FC8181; border: 1px solid rgba(229,62,62,0.3); }
.badge-medium { background: rgba(255,153,51,0.15); color: #F6AD55; border: 1px solid rgba(255,153,51,0.3); }
.badge-low { background: rgba(104,211,145,0.12); color: #68D391; border: 1px solid rgba(104,211,145,0.25); }

/* Section headers */
.section-head {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    color: #6B6B9A;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    border-bottom: 1px solid #1E1E35;
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
}

/* Alert row */
.alert-row {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    padding: 0.75rem 1rem;
    background: #0D0D14;
    border: 1px solid #1E1E35;
    border-radius: 8px;
    margin-bottom: 0.5rem;
    font-size: 0.85rem;
    color: #C8C8E0;
}

/* Connection status */
.conn-ok { color: #68D391; font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem; }
.conn-err { color: #FC8181; font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem; }
.conn-demo { color: #F6AD55; font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem; }

/* Override streamlit defaults */
.stPlotlyChart { background: transparent !important; }
div[data-testid="stAppViewContainer"] { background: #08080F; }
div[data-testid="block-container"] { background: #08080F; }
</style>
""", unsafe_allow_html=True)

# ─── Init DB ─────────────────────────────────────────────────────────────────
db, db_error = get_database()
demo_mode = db is None

# Sidebar
with st.sidebar:
    st.markdown("### 🗳️ Election Bias Audit")
    st.markdown("---")
    
    if demo_mode:
        st.markdown('<p class="conn-demo">◉ DEMO MODE — no MongoDB URI</p>', unsafe_allow_html=True)
        st.caption("Add MONGODB_URI to .env or st.secrets to connect Atlas")
    else:
        if st.button("🌱 Seed Database", use_container_width=True):
            with st.spinner("Seeding collections..."):
                results = seed_database(db)
                st.success(f"Seeded: {results}")
        st.markdown('<p class="conn-ok">● MongoDB Atlas connected</p>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("**Collections**")
    st.markdown("""
    - `elections` — state-level turnout  
    - `candidates` — 45K+ candidate records  
    - `audit_logs` — bias metrics per year  
    - `alerts` — threshold breach alerts  
    """)
    st.markdown("---")
    st.markdown("**Elections analysed**")
    for y in [1999, 2004, 2009, 2014, 2019, 2024]:
        st.markdown(f"• Lok Sabha {y}")

# ─── Header ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <div class="header-title">
        <span class="india">India</span> Election Bias Audit System
    </div>
    <div class="header-sub">
        MongoDB · PyMongo · Fairness Metrics · Lok Sabha 1999 – 2024
    </div>
</div>
""", unsafe_allow_html=True)

# ─── Load data ───────────────────────────────────────────────────────────────
audit_logs = get_audit_logs(db)
alerts = get_alerts(db)

df_logs = pd.DataFrame(audit_logs)
df_alerts = pd.DataFrame(alerts) if alerts else pd.DataFrame()

years = [log["election_year"] for log in audit_logs]
bias_scores = [log["bias_score"] for log in audit_logs]
gender_gaps = [log["fairness_metrics"]["gender"]["win_rate_gap"] for log in audit_logs]
female_shares = [log["fairness_metrics"]["gender"]["female_candidate_share"] for log in audit_logs]

latest = audit_logs[-1] if audit_logs else {}
prev = audit_logs[-2] if len(audit_logs) > 1 else audit_logs[-1]

# ─── KPI cards ───────────────────────────────────────────────────────────────
latest_bias = latest.get("bias_score", 0)
prev_bias = prev.get("bias_score", 0)
bias_delta = latest_bias - prev_bias
latest_gap = latest.get("fairness_metrics", {}).get("gender", {}).get("win_rate_gap", 0)
latest_share = latest.get("fairness_metrics", {}).get("gender", {}).get("female_candidate_share", 0)
high_alerts = sum(1 for a in alerts if a.get("severity") == "HIGH" and not a.get("resolved", True))

col1, col2, col3, col4 = st.columns(4)

with col1:
    delta_cls = "delta-down" if bias_delta > 0 else "delta-up"
    delta_sym = "▲" if bias_delta > 0 else "▼"
    st.markdown(f"""
    <div class="metric-card {'danger' if latest_bias > 0.4 else 'warning'}">
        <div class="metric-label">Overall Bias Score (2024)</div>
        <div class="metric-value">{latest_bias:.2f}</div>
        <div class="metric-delta {delta_cls}">{delta_sym} {abs(bias_delta):.3f} vs 2019</div>
    </div>""", unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card danger">
        <div class="metric-label">Gender Win-Rate Gap (2024)</div>
        <div class="metric-value">{latest_gap:.2f}</div>
        <div class="metric-delta delta-down">Male wins {latest_gap:.0%} more often</div>
    </div>""", unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card {'warning' if latest_share < 0.15 else 'info'}">
        <div class="metric-label">Female Candidate Share (2024)</div>
        <div class="metric-value">{latest_share:.0%}</div>
        <div class="metric-delta {'delta-down' if latest_share < 0.33 else 'delta-up'}">Target: 33% (Women's Reservation Bill)</div>
    </div>""", unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card {'danger' if high_alerts > 3 else 'warning'}">
        <div class="metric-label">Unresolved HIGH Alerts</div>
        <div class="metric-value">{high_alerts}</div>
        <div class="metric-delta delta-down">{len(alerts)} total alerts generated</div>
    </div>""", unsafe_allow_html=True)

# ─── Charts row 1 ────────────────────────────────────────────────────────────
st.markdown('<div class="section-head">Bias Score Trend · Lok Sabha 1999 – 2024</div>', unsafe_allow_html=True)

col_l, col_r = st.columns([3, 2])

with col_l:
    fig_trend = go.Figure()
    
    # Threshold band
    fig_trend.add_hrect(y0=0.35, y1=0.6, fillcolor="rgba(229,62,62,0.06)",
                        line_width=0, annotation_text="HIGH BIAS ZONE",
                        annotation_position="top left",
                        annotation_font=dict(size=9, color="#FC8181"))
    
    # Bias score line
    fig_trend.add_trace(go.Scatter(
        x=years, y=bias_scores,
        mode="lines+markers",
        name="Bias Score",
        line=dict(color="#FF9933", width=3),
        marker=dict(size=9, color="#FF9933", line=dict(color="#08080F", width=2)),
        fill="tozeroy", fillcolor="rgba(255,153,51,0.08)",
    ))
    
    # Gender gap line
    fig_trend.add_trace(go.Scatter(
        x=years, y=gender_gaps,
        mode="lines+markers",
        name="Gender Win-Rate Gap",
        line=dict(color="#FC8181", width=2, dash="dash"),
        marker=dict(size=7, color="#FC8181"),
    ))
    
    # Female candidate share
    fig_trend.add_trace(go.Scatter(
        x=years, y=female_shares,
        mode="lines+markers",
        name="Female Candidate Share",
        line=dict(color="#68D391", width=2),
        marker=dict(size=7, color="#68D391"),
    ))
    
    fig_trend.update_layout(
        plot_bgcolor="#0D0D14", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Mono", size=11, color="#6B6B9A"),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10), orientation="h", y=-0.15),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(gridcolor="#1E1E35", tickmode="array", tickvals=years,
                   tickfont=dict(size=10)),
        yaxis=dict(gridcolor="#1E1E35", tickformat=".2f"),
        hovermode="x unified",
    )
    st.plotly_chart(fig_trend, use_container_width=True)

with col_r:
    st.markdown('<div class="section-head">Component Bias Breakdown (2024)</div>', unsafe_allow_html=True)
    
    components = latest.get("component_scores", {})
    comp_labels = ["Gender Bias", "Representation Bias", "Caste Bias", "Regional Bias"]
    comp_keys = ["gender_bias", "representation_bias", "caste_bias", "regional_bias"]
    comp_vals = [components.get(k, 0) for k in comp_keys]
    comp_colors = ["#E53E3E", "#FF9933", "#F6AD55", "#4299E1"]
    
    fig_bar = go.Figure(go.Bar(
        x=comp_vals, y=comp_labels,
        orientation="h",
        marker=dict(color=comp_colors, opacity=0.85),
        text=[f"{v:.2f}" for v in comp_vals],
        textposition="outside",
        textfont=dict(family="IBM Plex Mono", size=11, color="#C8C8E0"),
    ))
    fig_bar.add_vline(x=0.35, line_color="#6B6B9A", line_dash="dash",
                      annotation_text="threshold", annotation_font=dict(size=9, color="#6B6B9A"))
    fig_bar.update_layout(
        plot_bgcolor="#0D0D14", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Mono", size=11, color="#6B6B9A"),
        margin=dict(l=10, r=60, t=10, b=10),
        xaxis=dict(gridcolor="#1E1E35", range=[0, 1.1]),
        yaxis=dict(gridcolor="rgba(0,0,0,0)"),
        showlegend=False,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ─── MongoDB showcase query ───────────────────────────────────────────────────
st.markdown('<div class="section-head">Live MongoDB Query — Bias Score Trend</div>', unsafe_allow_html=True)

with st.expander("View aggregation query", expanded=False):
    st.code("""
# Query 1: Bias score trend across elections
db.audit_logs.find(
    {},
    {"election_year": 1, "bias_score": 1, "fairness_metrics.gender": 1}
).sort("election_year", 1)

# Query 2: Find all HIGH severity unresolved alerts
db.alerts.find({
    "severity": "HIGH",
    "resolved": False
}).sort("election_year", 1)

# Query 3: Average bias by component across all elections
db.audit_logs.aggregate([
    {"$group": {
        "_id": None,
        "avg_bias": {"$avg": "$bias_score"},
        "avg_gender_bias": {"$avg": "$component_scores.gender_bias"},
        "avg_caste_bias": {"$avg": "$component_scores.caste_bias"},
    }}
])
""", language="python")

# ─── Alerts panel ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-head">Unresolved Alerts</div>', unsafe_allow_html=True)

unresolved = [a for a in alerts if not a.get("resolved", False)][:10]
if unresolved:
    for alert in unresolved:
        sev = alert.get("severity", "LOW")
        badge_cls = {"HIGH": "badge-high", "MEDIUM": "badge-medium", "LOW": "badge-low"}.get(sev, "badge-low")
        st.markdown(f"""
        <div class="alert-row">
            <span class="alert-badge {badge_cls}">{sev}</span>
            <span style="color:#8888AA;font-family:'IBM Plex Mono',monospace;font-size:0.78rem;">
                {alert.get('election_year')}
            </span>
            <span>{alert.get('description', alert.get('metric', ''))}</span>
        </div>""", unsafe_allow_html=True)
else:
    st.info("No unresolved alerts.")

# ─── Regional turnout heatmap ─────────────────────────────────────────────────
st.markdown('<div class="section-head">Regional Voter Turnout by Election Year</div>', unsafe_allow_html=True)

regions = ["North", "South", "East", "West", "NE"]
election_years = [log["election_year"] for log in audit_logs]
turnout_matrix = []
for log in audit_logs:
    r = log["fairness_metrics"]["regional"]
    turnout_matrix.append([
        r["north_turnout"], r["south_turnout"],
        r["east_turnout"], r["west_turnout"], r["ne_turnout"]
    ])

fig_heat = go.Figure(go.Heatmap(
    z=turnout_matrix,
    x=regions,
    y=[str(y) for y in election_years],
    colorscale=[[0, "#1A1A2E"], [0.4, "#FF9933"], [1.0, "#138808"]],
    text=[[f"{v:.1%}" for v in row] for row in turnout_matrix],
    texttemplate="%{text}",
    textfont=dict(family="IBM Plex Mono", size=11),
    showscale=True,
    colorbar=dict(tickformat=".0%", tickfont=dict(family="IBM Plex Mono", size=10))
))
fig_heat.update_layout(
    plot_bgcolor="#0D0D14", paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="IBM Plex Mono", size=11, color="#6B6B9A"),
    margin=dict(l=10, r=10, t=10, b=10),
    xaxis=dict(side="top"),
)
st.plotly_chart(fig_heat, use_container_width=True)

# Footer
st.markdown("---")
st.markdown(
    '<p style="font-family:IBM Plex Mono;font-size:0.72rem;color:#3A3A5C;text-align:center;">'
    'Indian Election Bias Audit System · MongoDB Atlas · ECI Open Data · '
    'Lok Sabha 1999–2024 · College Project</p>',
    unsafe_allow_html=True
)
