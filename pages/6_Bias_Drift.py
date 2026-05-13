"""
Page 6: Bias Drift Detector
The key academic framing: each election = a "model run". 
This page tracks whether the political system's output (who wins) 
is getting more or less biased — exactly like AI model version comparison.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.db import get_database, get_audit_logs

st.set_page_config(page_title="Bias Drift · India Election Audit", page_icon="📡", layout="wide")

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
.drift-card {
    background: #0D0D14; border: 1px solid #1E1E35; border-radius: 10px;
    padding: 1.2rem 1.4rem; text-align: center;
}
.drift-label { font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; color: #6B6B9A;
               text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.4rem; }
.drift-val { font-size: 1.8rem; font-weight: 800; }
.drift-sub { font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; margin-top: 0.3rem; }
.improved { color: #68D391; }
.worsened { color: #FC8181; }
.neutral { color: #F6AD55; }
.compare-panel {
    background: #0A0A12; border: 1px solid #1E1E35; border-radius: 10px;
    padding: 1.4rem; margin-bottom: 1rem;
}
.compare-header {
    font-size: 1.1rem; font-weight: 700; color: #F0F0FF;
    margin-bottom: 1rem; display: flex; align-items: center; gap: 0.6rem;
}
.metric-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 0.55rem 0; border-bottom: 1px solid #1A1A28;
    font-size: 0.85rem;
}
.metric-row:last-child { border-bottom: none; }
.metric-name { color: #8888AA; font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem; }
.metric-a { color: #4299E1; font-weight: 600; font-family: 'IBM Plex Mono', monospace; }
.metric-b { color: #FF9933; font-weight: 600; font-family: 'IBM Plex Mono', monospace; }
.delta-pill {
    padding: 0.1rem 0.5rem; border-radius: 20px;
    font-family: 'IBM Plex Mono', monospace; font-size: 0.70rem; font-weight: 600;
}
.pill-good { background: rgba(104,211,145,0.12); color: #68D391; }
.pill-bad  { background: rgba(252,129,129,0.12); color: #FC8181; }
.pill-flat { background: rgba(107,107,154,0.12); color: #9090B8; }
.framing-box {
    background: linear-gradient(135deg, #0A0A18 0%, #10101E 100%);
    border: 1px solid #2A2A45; border-radius: 10px;
    padding: 1.4rem; margin-bottom: 1.5rem;
    border-left: 3px solid #9F7AEA;
}
.framing-title { font-weight: 700; color: #C4B5FD; margin-bottom: 0.6rem; font-size: 0.95rem; }
.framing-body { color: #9090B8; font-size: 0.85rem; line-height: 1.7; }
</style>
""", unsafe_allow_html=True)

db, _ = get_database()
audit_logs = get_audit_logs(db)

st.markdown('<div class="page-title">📡 Bias Drift Detector</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Each election = one "model version". Track whether the system is getting fairer or more biased.</div>', unsafe_allow_html=True)

# ─── Academic framing box ─────────────────────────────────────────────────────
st.markdown("""
<div class="framing-box">
    <div class="framing-title">🎓 The AI Fairness Framing</div>
    <div class="framing-body">
        In machine learning, a <strong style="color:#C4B5FD;">bias audit</strong> compares model versions to detect 
        whether retraining introduced new fairness regressions. This page applies the same framework to elections: 
        each Lok Sabha election is treated as a <strong style="color:#C4B5FD;">model checkpoint</strong>, 
        and the political system is the model being audited. 
        The question is not just "is there bias?" but <strong style="color:#C4B5FD;">"is the bias improving or drifting?"</strong>
        — the exact same question asked in production ML monitoring systems.
    </div>
</div>
""", unsafe_allow_html=True)

years = [log["election_year"] for log in audit_logs]
year_labels = [str(y) for y in years]

# ─── Select two elections to compare ─────────────────────────────────────────
st.markdown('<div class="section-head">Election-to-Election Comparison (Version Diff)</div>', unsafe_allow_html=True)

col_a, col_b = st.columns(2)
with col_a:
    election_a = st.selectbox("Baseline Election (v1)", years[:-1], index=len(years)-3,
                               format_func=lambda y: f"Lok Sabha {y}")
with col_b:
    valid_b = [y for y in years if y > election_a]
    election_b = st.selectbox("Comparison Election (v2)", valid_b, index=len(valid_b)-1,
                               format_func=lambda y: f"Lok Sabha {y}")

log_a = next(l for l in audit_logs if l["election_year"] == election_a)
log_b = next(l for l in audit_logs if l["election_year"] == election_b)

def fmt_pct(v): return f"{v:.1%}"
def fmt_score(v): return f"{v:.3f}"

def delta_html(a, b, lower_is_better=True):
    diff = b - a
    if abs(diff) < 0.001:
        return '<span class="delta-pill pill-flat">≈ flat</span>'
    improved = (diff < 0) if lower_is_better else (diff > 0)
    cls = "pill-good" if improved else "pill-bad"
    sym = "▼" if diff < 0 else "▲"
    return f'<span class="delta-pill {cls}">{sym} {abs(diff):.3f}</span>'

metrics_compare = [
    ("Overall Bias Score",         log_a["bias_score"],                                   log_b["bias_score"],                                   True, fmt_score),
    ("Gender Win-Rate Gap",        log_a["fairness_metrics"]["gender"]["win_rate_gap"],    log_b["fairness_metrics"]["gender"]["win_rate_gap"],    True, fmt_pct),
    ("Female Candidate Share",     log_a["fairness_metrics"]["gender"]["female_candidate_share"], log_b["fairness_metrics"]["gender"]["female_candidate_share"], False, fmt_pct),
    ("Male Win Rate",              log_a["fairness_metrics"]["gender"]["male_win_rate"],   log_b["fairness_metrics"]["gender"]["male_win_rate"],   False, fmt_pct),
    ("Female Win Rate",            log_a["fairness_metrics"]["gender"]["female_win_rate"], log_b["fairness_metrics"]["gender"]["female_win_rate"], False, fmt_pct),
    ("Caste Max Gap",              log_a["fairness_metrics"]["caste"]["max_gap"],          log_b["fairness_metrics"]["caste"]["max_gap"],          True, fmt_pct),
    ("North–South Turnout Gap",    log_a["fairness_metrics"]["regional"]["north_south_gap"], log_b["fairness_metrics"]["regional"]["north_south_gap"], True, fmt_pct),
    ("Gender Bias Component",      log_a["component_scores"]["gender_bias"],               log_b["component_scores"]["gender_bias"],               True, fmt_score),
    ("Representation Bias",        log_a["component_scores"]["representation_bias"],       log_b["component_scores"]["representation_bias"],       True, fmt_score),
    ("Caste Bias Component",       log_a["component_scores"]["caste_bias"],                log_b["component_scores"]["caste_bias"],                True, fmt_score),
    ("Regional Bias Component",    log_a["component_scores"]["regional_bias"],             log_b["component_scores"]["regional_bias"],             True, fmt_score),
]

# Summary drift cards
improved = sum(1 for _, a, b, lib, _ in metrics_compare if (b < a if lib else b > a) and abs(b-a) > 0.001)
worsened = sum(1 for _, a, b, lib, _ in metrics_compare if (b > a if lib else b < a) and abs(b-a) > 0.001)
flat_n   = len(metrics_compare) - improved - worsened
bias_drift = log_b["bias_score"] - log_a["bias_score"]

c1, c2, c3, c4 = st.columns(4)
with c1:
    direction = "improved" if bias_drift < 0 else "worsened"
    cls = "improved" if bias_drift < 0 else "worsened"
    st.markdown(f"""<div class="drift-card">
        <div class="drift-label">Bias Score Drift</div>
        <div class="drift-val {cls}">{bias_drift:+.3f}</div>
        <div class="drift-sub {cls}">{direction}</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="drift-card">
        <div class="drift-label">Metrics Improved</div>
        <div class="drift-val improved">{improved}</div>
        <div class="drift-sub improved">of {len(metrics_compare)} tracked</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="drift-card">
        <div class="drift-label">Metrics Worsened</div>
        <div class="drift-val worsened">{worsened}</div>
        <div class="drift-sub worsened">regression detected</div>
    </div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div class="drift-card">
        <div class="drift-label">Years Span</div>
        <div class="drift-val neutral">{election_b - election_a}</div>
        <div class="drift-sub neutral">years between audits</div>
    </div>""", unsafe_allow_html=True)

st.markdown("")

# Metric-by-metric diff table
st.markdown(f"""
<div class="compare-panel">
  <div class="compare-header">
    <span style="background:#1A2A3A;padding:0.2rem 0.7rem;border-radius:4px;
                 font-family:'IBM Plex Mono',monospace;font-size:0.78rem;color:#4299E1;">
      v1 · {election_a}
    </span>
    <span style="color:#6B6B9A;">→</span>
    <span style="background:#2A1A0A;padding:0.2rem 0.7rem;border-radius:4px;
                 font-family:'IBM Plex Mono',monospace;font-size:0.78rem;color:#FF9933;">
      v2 · {election_b}
    </span>
    <span style="font-size:0.85rem;color:#6B6B9A;font-weight:400;margin-left:auto;">
      Metric-level diff
    </span>
  </div>
""", unsafe_allow_html=True)

for label, val_a, val_b, lib, fmt in metrics_compare:
    d_html = delta_html(val_a, val_b, lib)
    st.markdown(f"""
  <div class="metric-row">
    <span class="metric-name">{label}</span>
    <span class="metric-a">{fmt(val_a)}</span>
    <span style="color:#3A3A5C;">→</span>
    <span class="metric-b">{fmt(val_b)}</span>
    {d_html}
  </div>""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ─── Radar chart ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-head">Bias Component Radar — Side-by-Side</div>', unsafe_allow_html=True)

components = ["Gender Bias", "Representation Bias", "Caste Bias", "Regional Bias"]
vals_a = [log_a["component_scores"][k] for k in ["gender_bias", "representation_bias", "caste_bias", "regional_bias"]]
vals_b = [log_b["component_scores"][k] for k in ["gender_bias", "representation_bias", "caste_bias", "regional_bias"]]

fig_radar = go.Figure()
fig_radar.add_trace(go.Scatterpolar(
    r=vals_a + [vals_a[0]], theta=components + [components[0]],
    fill="toself", fillcolor="rgba(66,153,225,0.12)",
    line=dict(color="#4299E1", width=2.5),
    name=f"Lok Sabha {election_a}",
    marker=dict(size=7),
))
fig_radar.add_trace(go.Scatterpolar(
    r=vals_b + [vals_b[0]], theta=components + [components[0]],
    fill="toself", fillcolor="rgba(255,153,51,0.12)",
    line=dict(color="#FF9933", width=2.5, dash="dash"),
    name=f"Lok Sabha {election_b}",
    marker=dict(size=7),
))
fig_radar.update_layout(
    polar=dict(
        bgcolor="#0D0D14",
        radialaxis=dict(visible=True, range=[0, 1], gridcolor="#2A2A45",
                        tickfont=dict(family="IBM Plex Mono", size=9, color="#6B6B9A")),
        angularaxis=dict(gridcolor="#2A2A45",
                         tickfont=dict(family="IBM Plex Mono", size=10, color="#C8C8E0")),
    ),
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="IBM Plex Mono", size=11, color="#6B6B9A"),
    legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=-0.08),
    margin=dict(l=40, r=40, t=20, b=20),
)
st.plotly_chart(fig_radar, use_container_width=True)

# ─── Full timeline drift waterfall ───────────────────────────────────────────
st.markdown('<div class="section-head">Bias Score Drift — Election-to-Election Waterfall</div>', unsafe_allow_html=True)

bias_scores = [log["bias_score"] for log in audit_logs]
deltas = [0] + [bias_scores[i] - bias_scores[i-1] for i in range(1, len(bias_scores))]
colors = ["#68D391" if d < -0.001 else "#FC8181" if d > 0.001 else "#6B6B9A" for d in deltas]
labels = [f"{'+' if d >= 0 else ''}{d:.3f}" if i > 0 else "baseline" for i, d in enumerate(deltas)]

fig_wf = go.Figure()
# Running total line
fig_wf.add_trace(go.Scatter(
    x=year_labels, y=bias_scores,
    mode="lines", name="Running bias score",
    line=dict(color="#6B6B9A", width=1.5, dash="dot"),
))
# Delta bars
fig_wf.add_trace(go.Bar(
    x=year_labels, y=deltas,
    name="Election drift",
    marker=dict(color=colors, opacity=0.85),
    text=labels,
    textposition="outside",
    textfont=dict(family="IBM Plex Mono", size=10, color="#C8C8E0"),
))
fig_wf.add_hline(y=0, line_color="#2A2A45", line_width=1)
fig_wf.update_layout(
    plot_bgcolor="#0D0D14", paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="IBM Plex Mono", size=11, color="#6B6B9A"),
    legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=-0.15),
    margin=dict(l=10, r=10, t=10, b=10),
    xaxis=dict(gridcolor="#1E1E35"),
    yaxis=dict(gridcolor="#1E1E35", tickformat=".3f", title="Bias delta"),
    hovermode="x unified",
    barmode="overlay",
)
st.plotly_chart(fig_wf, use_container_width=True)

# ─── MongoDB query ────────────────────────────────────────────────────────────
st.markdown('<div class="section-head">MongoDB Query — Drift Detection</div>', unsafe_allow_html=True)
with st.expander("View drift query"):
    st.code(f"""
# Fetch two audit logs for drift comparison
log_a = db.audit_logs.find_one({{"election_year": {election_a}}})
log_b = db.audit_logs.find_one({{"election_year": {election_b}}})

# Compute drift across all component scores
drift = {{}}
for component in ["gender_bias", "representation_bias", "caste_bias", "regional_bias"]:
    drift[component] = {{
        "baseline":   log_a["component_scores"][component],
        "comparison": log_b["component_scores"][component],
        "delta":      log_b["component_scores"][component] - log_a["component_scores"][component],
        "direction":  "improved" if log_b["component_scores"][component] < log_a["component_scores"][component] else "worsened"
    }}

# Overall bias drift
drift["overall"] = log_b["bias_score"] - log_a["bias_score"]

# ── Equivalent MongoDB aggregation ──
db.audit_logs.aggregate([
    {{"$match": {{"election_year": {{"$in": [{election_a}, {election_b}]}}}}}},
    {{"$sort": {{"election_year": 1}}}},
    {{"$group": {{
        "_id": None,
        "logs": {{"$push": {{"year": "$election_year", "score": "$bias_score",
                            "components": "$component_scores"}}}}
    }}}}
])
""", language="python")
