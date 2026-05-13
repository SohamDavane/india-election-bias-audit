"""
Page 5: Alerts Management
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.db import get_database, get_alerts, get_audit_logs

st.set_page_config(page_title="Alerts · India Election Audit", page_icon="🚨", layout="wide")

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
.alert-card {
    background: #0D0D14; border: 1px solid #1E1E35; border-radius: 10px;
    padding: 1rem 1.2rem; margin-bottom: 0.6rem;
    display: flex; gap: 1rem; align-items: flex-start;
}
.alert-card.high { border-left: 3px solid #E53E3E; }
.alert-card.medium { border-left: 3px solid #FF9933; }
.alert-card.low { border-left: 3px solid #68D391; }
.alert-badge {
    display: inline-block; padding: 0.2rem 0.6rem; border-radius: 4px;
    font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; font-weight: 500;
    white-space: nowrap;
}
.badge-HIGH { background: rgba(229,62,62,0.15); color: #FC8181; border: 1px solid rgba(229,62,62,0.3); }
.badge-MEDIUM { background: rgba(255,153,51,0.15); color: #F6AD55; border: 1px solid rgba(255,153,51,0.3); }
.badge-LOW { background: rgba(104,211,145,0.12); color: #68D391; border: 1px solid rgba(104,211,145,0.25); }
.alert-resolved { opacity: 0.4; }
.alert-metric { font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem; color: #8888AA; }
.alert-value { font-size: 1.1rem; font-weight: 700; color: #F0F0FF; }
.alert-year { font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem; color: #6B6B9A; }
</style>
""", unsafe_allow_html=True)

db, _ = get_database()
all_alerts = get_alerts(db)

st.markdown('<div class="page-title">🚨 Alerts & Threshold Breaches</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Auto-generated when fairness metrics cross defined thresholds</div>', unsafe_allow_html=True)

# Filters in sidebar
with st.sidebar:
    st.markdown("### Filter Alerts")
    sev_filter = st.multiselect("Severity", ["HIGH", "MEDIUM", "LOW"], default=["HIGH", "MEDIUM"])
    status_filter = st.radio("Status", ["All", "Unresolved only", "Resolved only"])

# Apply filters
filtered = all_alerts
if sev_filter:
    filtered = [a for a in filtered if a.get("severity") in sev_filter]
if status_filter == "Unresolved only":
    filtered = [a for a in filtered if not a.get("resolved", False)]
elif status_filter == "Resolved only":
    filtered = [a for a in filtered if a.get("resolved", False)]

# ─── KPIs ─────────────────────────────────────────────────────────────────────
total = len(all_alerts)
high = sum(1 for a in all_alerts if a.get("severity") == "HIGH")
medium = sum(1 for a in all_alerts if a.get("severity") == "MEDIUM")
unresolved = sum(1 for a in all_alerts if not a.get("resolved", False))

c1, c2, c3, c4 = st.columns(4)
for col, label, val, color in [
    (c1, "Total Alerts", total, "#6B6B9A"),
    (c2, "HIGH Severity", high, "#FC8181"),
    (c3, "MEDIUM Severity", medium, "#F6AD55"),
    (c4, "Unresolved", unresolved, "#FF9933"),
]:
    with col:
        st.markdown(f"""
        <div style="background:#0D0D14;border:1px solid #1E1E35;border-radius:10px;
                    padding:1rem 1.2rem;border-left:3px solid {color};">
            <div style="font-family:'IBM Plex Mono',monospace;font-size:0.68rem;
                        color:#6B6B9A;text-transform:uppercase;letter-spacing:0.1em;">{label}</div>
            <div style="font-size:2rem;font-weight:800;color:{color};">{val}</div>
        </div>""", unsafe_allow_html=True)

# ─── Alert severity distribution ──────────────────────────────────────────────
st.markdown("")
col_l, col_r = st.columns([2, 1])

with col_l:
    st.markdown('<div class="section-head">Alert Volume by Election Year & Severity</div>', unsafe_allow_html=True)
    df_a = pd.DataFrame(all_alerts)
    if not df_a.empty and "election_year" in df_a.columns:
        pivot = df_a.groupby(["election_year", "severity"]).size().reset_index(name="count")
        years_u = sorted(pivot["election_year"].unique())
        
        fig = go.Figure()
        for sev, color in [("HIGH", "#E53E3E"), ("MEDIUM", "#FF9933"), ("LOW", "#68D391")]:
            sev_data = pivot[pivot["severity"] == sev]
            fig.add_trace(go.Bar(
                x=[str(y) for y in sev_data["election_year"].tolist()],
                y=sev_data["count"].tolist(),
                name=sev, marker_color=color, opacity=0.85,
            ))
        
        fig.update_layout(
            barmode="stack", plot_bgcolor="#0D0D14", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="IBM Plex Mono", size=11, color="#6B6B9A"),
            legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=-0.15),
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(gridcolor="#1E1E35"),
            yaxis=dict(gridcolor="#1E1E35", title="Alert Count"),
        )
        st.plotly_chart(fig, use_container_width=True)

with col_r:
    st.markdown('<div class="section-head">By Metric Type</div>', unsafe_allow_html=True)
    if not df_a.empty and "metric" in df_a.columns:
        metric_counts = df_a["metric"].value_counts().head(6)
        fig2 = go.Figure(go.Bar(
            x=metric_counts.values.tolist(),
            y=metric_counts.index.tolist(),
            orientation="h",
            marker=dict(color="#FF9933", opacity=0.8),
            text=metric_counts.values.tolist(),
            textposition="outside",
            textfont=dict(family="IBM Plex Mono", size=10, color="#C8C8E0"),
        ))
        fig2.update_layout(
            plot_bgcolor="#0D0D14", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="IBM Plex Mono", size=11, color="#6B6B9A"),
            margin=dict(l=10, r=40, t=10, b=10),
            xaxis=dict(gridcolor="#1E1E35"),
            yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(size=10)),
            showlegend=False,
        )
        st.plotly_chart(fig2, use_container_width=True)

# ─── Alert list ───────────────────────────────────────────────────────────────
st.markdown(f'<div class="section-head">Alert Log — {len(filtered)} results</div>', unsafe_allow_html=True)

for alert in filtered[:30]:
    sev = alert.get("severity", "LOW")
    resolved = alert.get("resolved", False)
    card_cls = f"alert-card {sev.lower()}"
    badge_cls = f"badge-{sev}"
    resolved_tag = '<span style="font-family:IBM Plex Mono;font-size:0.68rem;color:#68D391;">✓ resolved</span>' if resolved else ''
    
    actual = alert.get("actual_value", 0)
    threshold = alert.get("threshold", 0)
    direction = alert.get("direction", "above")
    
    st.markdown(f"""
    <div class="{card_cls} {'alert-resolved' if resolved else ''}">
        <div style="min-width:70px;">
            <span class="alert-badge {badge_cls}">{sev}</span>
        </div>
        <div style="flex:1;">
            <div style="display:flex;gap:0.8rem;align-items:center;margin-bottom:0.3rem;">
                <span class="alert-year">{alert.get('election_year')}</span>
                <code style="font-size:0.75rem;color:#8888AA;background:rgba(255,255,255,0.04);
                             padding:0.1rem 0.4rem;border-radius:3px;">{alert.get('metric', '')}</code>
                {resolved_tag}
            </div>
            <div style="font-size:0.88rem;color:#C8C8E0;">
                Actual: <strong style="color:#F0F0FF;">{actual:.3f}</strong>
                &nbsp;{direction}&nbsp;threshold&nbsp;<strong style="color:#6B6B9A;">{threshold}</strong>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─── MongoDB query ────────────────────────────────────────────────────────────
st.markdown('<div class="section-head">MongoDB Query — Unresolved HIGH Alerts</div>', unsafe_allow_html=True)
with st.expander("View query"):
    st.code("""
# Get all unresolved HIGH severity alerts sorted by year
db.alerts.find(
    {"severity": "HIGH", "resolved": False}
).sort("election_year", 1)

# Count alerts by severity
db.alerts.aggregate([
    {"$group": {
        "_id": "$severity",
        "count": {"$sum": 1},
        "unresolved": {"$sum": {"$cond": [{"$eq": ["$resolved", False]}, 1, 0]}}
    }}
])
""", language="python")
