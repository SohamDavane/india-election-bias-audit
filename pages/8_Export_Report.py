"""
Page 8: PDF Report Exporter
Generates a downloadable audit report for any election year using ReportLab.
"""
import streamlit as st
import io
from datetime import datetime
from utils.db import get_database, get_audit_logs, get_alerts

st.set_page_config(page_title="Export Report · India Election Audit", page_icon="📄", layout="wide")

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
.preview-section {
    background: #0D0D14; border: 1px solid #1E1E35; border-radius: 10px;
    padding: 1.4rem; margin-bottom: 1rem;
}
.preview-title { font-size: 1rem; font-weight: 700; color: #F0F0FF; margin-bottom: 0.8rem; }
.metric-line {
    display: flex; justify-content: space-between; padding: 0.45rem 0;
    border-bottom: 1px solid #1A1A28; font-size: 0.84rem;
}
.metric-line:last-child { border-bottom: none; }
.m-label { color: #8888AA; font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem; }
.m-value { color: #F0F0FF; font-family: 'IBM Plex Mono', monospace; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

db, _ = get_database()
audit_logs = get_audit_logs(db)
all_alerts = get_alerts(db)

st.markdown('<div class="page-title">📄 Export Audit Report</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Generate a downloadable PDF bias audit report for any election year</div>', unsafe_allow_html=True)

# ─── Election selector ────────────────────────────────────────────────────────
years = [log["election_year"] for log in audit_logs]
col1, col2 = st.columns([2, 3])

with col1:
    selected_year = st.selectbox("Select Election Year", years, index=len(years)-1,
                                  format_func=lambda y: f"Lok Sabha {y}")
    report_author = st.text_input("Analyst Name", value="Election Bias Audit System")
    include_alerts = st.checkbox("Include alert log", value=True)
    include_party  = st.checkbox("Include party breakdown", value=True)

log = next(l for l in audit_logs if l["election_year"] == selected_year)
gender = log["fairness_metrics"]["gender"]
caste  = log["fairness_metrics"]["caste"]
regional = log["fairness_metrics"]["regional"]
components = log["component_scores"]
year_alerts = [a for a in all_alerts if a.get("election_year") == selected_year]

with col2:
    # Report preview
    bias_flag_text = "⚠ BIAS DETECTED" if log["bias_flag"] else "✓ WITHIN THRESHOLD"
    bias_color = "#FC8181" if log["bias_flag"] else "#68D391"
    
    st.markdown(f"""
    <div class="preview-section">
        <div class="preview-title">
            Report Preview — Lok Sabha {selected_year}
            <span style="margin-left:0.8rem;font-size:0.75rem;color:{bias_color};
                         font-family:'IBM Plex Mono',monospace;">{bias_flag_text}</span>
        </div>
        <div class="metric-line">
            <span class="m-label">Overall Bias Score</span>
            <span class="m-value" style="color:{bias_color};">{log['bias_score']:.4f}</span>
        </div>
        <div class="metric-line">
            <span class="m-label">Gender Win-Rate Gap</span>
            <span class="m-value">{gender['win_rate_gap']:.2%}</span>
        </div>
        <div class="metric-line">
            <span class="m-label">Female Candidate Share</span>
            <span class="m-value">{gender['female_candidate_share']:.2%}</span>
        </div>
        <div class="metric-line">
            <span class="m-label">Male Win Rate</span>
            <span class="m-value">{gender['male_win_rate']:.2%}</span>
        </div>
        <div class="metric-line">
            <span class="m-label">Female Win Rate</span>
            <span class="m-value">{gender['female_win_rate']:.2%}</span>
        </div>
        <div class="metric-line">
            <span class="m-label">Caste Max Gap</span>
            <span class="m-value">{caste['max_gap']:.2%}</span>
        </div>
        <div class="metric-line">
            <span class="m-label">North–South Turnout Gap</span>
            <span class="m-value">{regional['north_south_gap']:.2%}</span>
        </div>
        <div class="metric-line">
            <span class="m-label">Total Candidates Audited</span>
            <span class="m-value">{log['total_candidates']:,}</span>
        </div>
        <div class="metric-line">
            <span class="m-label">Alerts Generated</span>
            <span class="m-value">{len(year_alerts)}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─── Generate PDF ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-head">Generate PDF Report</div>', unsafe_allow_html=True)

def generate_pdf(log, year_alerts, author, include_alerts_flag, include_party_flag):
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             rightMargin=2*cm, leftMargin=2*cm,
                             topMargin=2*cm, bottomMargin=2*cm)

    # ── Styles ─────────────────────────────────────────────────────────────────
    styles = getSampleStyleSheet()
    
    SAFFRON = colors.HexColor("#FF9933")
    GREEN   = colors.HexColor("#138808")
    NAVY    = colors.HexColor("#0A0A20")
    LIGHT   = colors.HexColor("#F5F5FA")
    MUTED   = colors.HexColor("#888888")
    RED     = colors.HexColor("#E53E3E")
    TEAL    = colors.HexColor("#2B6CB0")

    title_style = ParagraphStyle("title", parent=styles["Title"],
                                  fontSize=22, textColor=NAVY, spaceAfter=4,
                                  fontName="Helvetica-Bold")
    subtitle_style = ParagraphStyle("subtitle", parent=styles["Normal"],
                                     fontSize=10, textColor=MUTED, spaceAfter=2)
    h1_style = ParagraphStyle("h1", parent=styles["Heading1"],
                               fontSize=14, textColor=NAVY, spaceAfter=6, spaceBefore=14,
                               fontName="Helvetica-Bold",
                               borderPad=4)
    h2_style = ParagraphStyle("h2", parent=styles["Heading2"],
                               fontSize=11, textColor=TEAL, spaceAfter=4, spaceBefore=8,
                               fontName="Helvetica-Bold")
    body_style = ParagraphStyle("body", parent=styles["Normal"],
                                 fontSize=9.5, textColor=colors.HexColor("#222222"),
                                 spaceAfter=4, leading=14)
    caption_style = ParagraphStyle("caption", parent=styles["Normal"],
                                    fontSize=8, textColor=MUTED, spaceAfter=2, fontName="Helvetica-Oblique")
    flag_style = ParagraphStyle("flag", parent=styles["Normal"],
                                 fontSize=11, fontName="Helvetica-Bold",
                                 textColor=RED if log["bias_flag"] else GREEN,
                                 spaceAfter=6)
    
    story = []
    gender = log["fairness_metrics"]["gender"]
    caste  = log["fairness_metrics"]["caste"]
    regional = log["fairness_metrics"]["regional"]
    components = log["component_scores"]
    yr = log["election_year"]

    # ── Cover ──────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=3, color=SAFFRON))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(f"Indian Election Bias Audit", title_style))
    story.append(Paragraph(f"Lok Sabha {yr} — Fairness Assessment Report", subtitle_style))
    story.append(Spacer(1, 0.2*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#DDDDDD")))
    story.append(Spacer(1, 0.4*cm))

    meta = [
        ["Analyst:", author],
        ["Generated:", datetime.now().strftime("%d %B %Y, %H:%M")],
        ["Election:", f"Lok Sabha General Election {yr}"],
        ["Candidates Audited:", f"{log['total_candidates']:,}"],
        ["Database:", "MongoDB Atlas · election_bias_audit"],
        ["Data Source:", "ECI Open Data (Pattern-matched, 1999–2024)"],
    ]
    meta_table = Table(meta, colWidths=[4*cm, 12*cm])
    meta_table.setStyle(TableStyle([
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("TEXTCOLOR", (0,0), (0,-1), MUTED),
        ("TEXTCOLOR", (1,0), (1,-1), NAVY),
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("TOPPADDING", (0,0), (-1,-1), 3),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.5*cm))

    bias_verdict = "BIAS DETECTED — Threshold exceeded in one or more fairness dimensions." \
                   if log["bias_flag"] else \
                   "WITHIN THRESHOLD — No critical bias flags raised for this election."
    story.append(Paragraph(f"Verdict: {bias_verdict}", flag_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#DDDDDD")))

    # ── Executive Summary ──────────────────────────────────────────────────────
    story.append(Paragraph("1. Executive Summary", h1_style))
    story.append(Paragraph(
        f"This report presents the results of a comprehensive bias audit conducted on the "
        f"Lok Sabha {yr} General Election dataset. The audit applies AI fairness methodologies "
        f"— specifically demographic parity, equal opportunity, and win-rate gap metrics — "
        f"to evaluate whether the electoral process produced equitable outcomes across gender, "
        f"caste, and regional dimensions.",
        body_style
    ))
    story.append(Paragraph(
        f"The overall bias score for Lok Sabha {yr} is <b>{log['bias_score']:.4f}</b> "
        f"(threshold: 0.40). A score above the threshold indicates systemic disparity "
        f"requiring attention. The gender dimension contributes most significantly to the "
        f"composite score, consistent with patterns across all six elections audited.",
        body_style
    ))

    # ── Overall Bias Score ─────────────────────────────────────────────────────
    story.append(Paragraph("2. Overall Bias Score", h1_style))
    
    score_data = [
        ["Component", "Score", "Weight", "Contribution", "Status"],
        ["Gender Bias",         f"{components['gender_bias']:.4f}",         "35%",
         f"{components['gender_bias']*0.35:.4f}",
         "HIGH" if components['gender_bias'] > 0.5 else ("MED" if components['gender_bias'] > 0.3 else "OK")],
        ["Representation Bias", f"{components['representation_bias']:.4f}", "30%",
         f"{components['representation_bias']*0.30:.4f}",
         "HIGH" if components['representation_bias'] > 0.5 else ("MED" if components['representation_bias'] > 0.3 else "OK")],
        ["Caste Bias",          f"{components['caste_bias']:.4f}",          "20%",
         f"{components['caste_bias']*0.20:.4f}",
         "HIGH" if components['caste_bias'] > 0.5 else ("MED" if components['caste_bias'] > 0.3 else "OK")],
        ["Regional Bias",       f"{components['regional_bias']:.4f}",       "15%",
         f"{components['regional_bias']*0.15:.4f}",
         "HIGH" if components['regional_bias'] > 0.5 else ("MED" if components['regional_bias'] > 0.3 else "OK")],
        ["COMPOSITE SCORE",     f"{log['bias_score']:.4f}",                 "100%",
         f"{log['bias_score']:.4f}", "FLAG" if log['bias_flag'] else "PASS"],
    ]
    
    score_table = Table(score_data, colWidths=[5*cm, 2.5*cm, 2*cm, 3*cm, 3.5*cm])
    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), NAVY),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("ALIGN", (1,0), (-1,-1), "CENTER"),
        ("ROWBACKGROUNDS", (0,1), (-1,-2), [LIGHT, colors.white]),
        ("BACKGROUND", (0,-1), (-1,-1), colors.HexColor("#E8E8F0")),
        ("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold"),
        ("TEXTCOLOR", (-1,-1), (-1,-1), RED if log["bias_flag"] else GREEN),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING", (0,0), (-1,-1), 5),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 0.3*cm))

    # ── Gender Bias ────────────────────────────────────────────────────────────
    story.append(Paragraph("3. Gender Bias Analysis", h1_style))
    story.append(Paragraph(
        f"Gender analysis compares win rates and representation between male and female candidates. "
        f"In Lok Sabha {yr}, female candidates comprised <b>{gender['female_candidate_share']:.1%}</b> "
        f"of total contestants — far below the 33% mandated by the Women's Reservation Bill. "
        f"The win-rate gap of <b>{gender['win_rate_gap']:.1%}</b> indicates that male candidates "
        f"are significantly more likely to win, independent of vote share.",
        body_style
    ))
    
    gender_data = [
        ["Metric", "Male", "Female", "Gap"],
        ["Win Rate",        f"{gender['male_win_rate']:.2%}",         f"{gender['female_win_rate']:.2%}",    f"{gender['win_rate_gap']:.2%}"],
        ["Candidate Count", f"{gender['male_candidate_count']:,}",     f"{gender['female_candidate_count']:,}", f"{gender['female_candidate_share']:.1%} share"],
    ]
    g_table = Table(gender_data, colWidths=[5*cm, 3.5*cm, 3.5*cm, 4*cm])
    g_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), TEAL),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9.5),
        ("ALIGN", (1,0), (-1,-1), "CENTER"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [LIGHT, colors.white]),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(g_table)

    # ── Caste Analysis ─────────────────────────────────────────────────────────
    story.append(Paragraph("4. Caste Category Analysis", h1_style))
    caste_rates = caste["win_rates_by_category"]
    
    caste_data = [["Caste Category", "Win Rate", "vs General"]]
    general_rate = caste_rates.get("General", 0)
    for cat in ["General", "OBC", "SC", "ST"]:
        rate = caste_rates.get(cat, 0)
        diff = rate - general_rate
        diff_str = f"{diff:+.2%}" if cat != "General" else "—"
        caste_data.append([cat, f"{rate:.2%}", diff_str])
    caste_data.append(["Max Gap", f"{caste['max_gap']:.2%}", ""])
    
    c_table = Table(caste_data, colWidths=[5*cm, 4*cm, 7*cm])
    c_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), NAVY),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9.5),
        ("ALIGN", (1,0), (-1,-1), "CENTER"),
        ("ROWBACKGROUNDS", (0,1), (-1,-2), [LIGHT, colors.white]),
        ("BACKGROUND", (0,-1), (-1,-1), colors.HexColor("#E8E8F0")),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(c_table)

    # ── Regional Analysis ──────────────────────────────────────────────────────
    story.append(Paragraph("5. Regional Voter Turnout", h1_style))
    story.append(Paragraph(
        f"Regional turnout disparity reflects unequal civic participation across India's "
        f"geographic zones. The North–South gap of <b>{regional['north_south_gap']:.1%}</b> "
        f"is the largest persistent disparity, with Northeast India consistently showing "
        f"the highest engagement at {regional['ne_turnout']:.1%}.",
        body_style
    ))
    
    reg_data = [
        ["Region", "Turnout", "vs National Avg"],
    ]
    nat_avg = (regional['north_turnout'] + regional['south_turnout'] + 
               regional['east_turnout'] + regional['west_turnout'] + regional['ne_turnout']) / 5
    for region_name, key in [("North", "north_turnout"), ("South", "south_turnout"),
                               ("East", "east_turnout"), ("West", "west_turnout"), ("NE", "ne_turnout")]:
        val = regional[key]
        diff = val - nat_avg
        reg_data.append([region_name, f"{val:.1%}", f"{diff:+.1%}"])
    reg_data.append(["North–South Gap", f"{regional['north_south_gap']:.1%}", ""])
    
    r_table = Table(reg_data, colWidths=[5*cm, 4*cm, 7*cm])
    r_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#276749")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9.5),
        ("ALIGN", (1,0), (-1,-1), "CENTER"),
        ("ROWBACKGROUNDS", (0,1), (-1,-2), [LIGHT, colors.white]),
        ("BACKGROUND", (0,-1), (-1,-1), colors.HexColor("#E8E8F0")),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(r_table)

    # ── Alerts ────────────────────────────────────────────────────────────────
    if include_alerts_flag and year_alerts:
        story.append(PageBreak())
        story.append(Paragraph("6. Alert Log", h1_style))
        story.append(Paragraph(
            f"The following {len(year_alerts)} alert(s) were automatically generated when "
            f"fairness metrics exceeded defined thresholds for Lok Sabha {yr}.",
            body_style
        ))
        
        alert_data = [["Severity", "Metric", "Threshold", "Actual", "Direction", "Resolved"]]
        for a in year_alerts:
            alert_data.append([
                a.get("severity", ""),
                a.get("metric", ""),
                str(a.get("threshold", "")),
                f"{a.get('actual_value', 0):.3f}",
                a.get("direction", "above"),
                "Yes" if a.get("resolved") else "No",
            ])
        
        a_table = Table(alert_data, colWidths=[2*cm, 4.5*cm, 2.5*cm, 2.5*cm, 2*cm, 2.5*cm])
        def sev_color(s):
            return RED if s == "HIGH" else colors.HexColor("#E07B00") if s == "MEDIUM" else GREEN
        
        a_style = [
            ("BACKGROUND", (0,0), (-1,0), NAVY),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 8.5),
            ("ALIGN", (2,0), (-1,-1), "CENTER"),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [LIGHT, colors.white]),
            ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ("TOPPADDING", (0,0), (-1,-1), 5),
        ]
        for i, a in enumerate(year_alerts, 1):
            a_style.append(("TEXTCOLOR", (0,i), (0,i), sev_color(a.get("severity", ""))))
            a_style.append(("FONTNAME", (0,i), (0,i), "Helvetica-Bold"))
        
        a_table.setStyle(TableStyle(a_style))
        story.append(a_table)

    # ── Methodology ───────────────────────────────────────────────────────────
    story.append(Paragraph("7. Methodology & AI Fairness Framework", h1_style))
    story.append(Paragraph(
        "This audit applies the same frameworks used in production ML model monitoring systems. "
        "Each election is treated as a 'model checkpoint', and the political system is audited "
        "for fairness regressions — exactly as an AI team would track bias across model versions.",
        body_style
    ))
    
    method_data = [
        ["Metric", "Definition", "Formula"],
        ["Win-Rate Gap",       "Difference in win probability between groups", "win_rate(A) - win_rate(B)"],
        ["Demographic Parity", "Equal positive prediction rates across groups", "P(win|male) - P(win|female)"],
        ["Representation Gap", "Candidate share vs 50% equitable baseline",    "(0.5 - female_share) / 0.5"],
        ["Caste Disparity",    "Max win-rate spread across caste categories",   "max(rates) - min(rates)"],
        ["Regional Gap",       "Absolute turnout difference across regions",    "|turnout_A - turnout_B|"],
        ["Composite Score",    "Weighted average of all normalized gaps",       "0.35G + 0.30R + 0.20C + 0.15Reg"],
    ]
    m_table = Table(method_data, colWidths=[4*cm, 6.5*cm, 5.5*cm])
    m_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), NAVY),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 8.5),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [LIGHT, colors.white]),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING", (0,0), (-1,-1), 5),
    ]))
    story.append(m_table)

    # ── Footer ─────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=2, color=SAFFRON))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        f"Indian Election Bias Audit System · MongoDB Atlas · "
        f"Generated {datetime.now().strftime('%d %B %Y')} · {author}",
        caption_style
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


if st.button("🔴 Generate PDF Report", use_container_width=True, type="primary"):
    with st.spinner("Generating report with ReportLab..."):
        try:
            pdf_bytes = generate_pdf(log, year_alerts, report_author, include_alerts, include_party)
            fname = f"election_bias_audit_{selected_year}.pdf"
            st.download_button(
                label=f"⬇ Download {fname}",
                data=pdf_bytes,
                file_name=fname,
                mime="application/pdf",
                use_container_width=True,
            )
            st.success(f"Report generated — {len(pdf_bytes)//1024} KB · {len(year_alerts)} alerts included")
        except ImportError:
            st.error("ReportLab not installed. Run: pip install reportlab")
        except Exception as e:
            st.error(f"Report generation failed: {e}")
            raise e

# ─── What's in the PDF ────────────────────────────────────────────────────────
st.markdown('<div class="section-head">Report Contents</div>', unsafe_allow_html=True)
st.markdown("""
The generated PDF contains:

1. **Cover page** — metadata, analyst name, election year, verdict badge  
2. **Executive summary** — plain-language interpretation of the bias score  
3. **Overall bias score table** — all 4 components with weights and contributions  
4. **Gender bias analysis** — win-rate table + candidate composition  
5. **Caste category analysis** — win rates across General / OBC / SC / ST  
6. **Regional turnout** — all 5 regions vs national average  
7. **Alert log** *(optional)* — every threshold breach with severity  
8. **Methodology** — the AI fairness framework equations used  
""")
