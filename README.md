# 🗳️ Indian Election Bias Audit System

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![MongoDB](https://img.shields.io/badge/MongoDB-Local%20%7C%20Atlas-green?style=flat-square&logo=mongodb)
![Streamlit](https://img.shields.io/badge/Streamlit-1.57-red?style=flat-square&logo=streamlit)
![Plotly](https://img.shields.io/badge/Plotly-6.7-blueviolet?style=flat-square&logo=plotly)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

> An AI fairness audit system applied to Indian Lok Sabha elections (1999–2024), tracking gender, caste, regional and party representation bias across 45,000+ candidate records using MongoDB.

---

## 🖥️ Live Demo

🔗 **[View Live App →](https://india-election-bias-audit.streamlit.app/)**

---

## 📸 Screenshots

<img width="1537" height="826" alt="image" src="https://github.com/user-attachments/assets/1cc624c9-db8f-4e50-abec-aa3a12bac9ea" />

<img width="1885" height="817" alt="image" src="https://github.com/user-attachments/assets/dcf9e34f-0f0c-409e-8901-3f4841d8bb9c" />

---

## 🎯 What This Project Does

Every election is treated as a **model checkpoint** — the same framework used in production ML fairness monitoring. The system audits whether the political system's output (who wins) is biased relative to its input (who stands), tracking drift across 6 elections.

**5 Fairness Metrics computed:**

| Metric | Formula | Threshold |
|---|---|---|
| Gender Win-Rate Gap | male_win_rate − female_win_rate | > 30% |
| Female Candidate Share | female / total candidates | < 15% |
| Caste Max Gap | max(caste_win_rates) − min | > 10% |
| North–South Turnout Gap | abs(north − south turnout) | > 8% |
| Composite Bias Score | Weighted average of all gaps | > 0.40 |

---

## 🗂️ MongoDB Collections

```
election_bias_audit/
├── elections       → State-level voter turnout (120 docs)
├── candidates      → Individual candidate records (45,000+ docs)
├── audit_logs      → Computed fairness metrics per election (6 docs)
└── alerts          → Auto-generated threshold breach alerts
```

**Why MongoDB?** Each election's `audit_log` document has a different `fairness_metrics` shape — 1999 data doesn't have the same party breakdown as 2024. MongoDB's flexible schema handles this naturally. A SQL table would require ALTER TABLE or NULL-heavy rows.

---

## 📊 Dashboard Pages

| Page | Description |
|---|---|
| 🏠 Overview | Bias score trend, component breakdown, regional heatmap |
| ♀ Gender Bias | Win-rate gaps, candidate share, state-level analysis |
| 🏛 Party Scorecard | Which parties field women? Fairness grades A/B/C |
| 🗺 Caste & Regional | SC/ST/OBC/General win rates, turnout by region |
| 🚨 Alerts | Threshold breach log with severity filtering |
| 🍃 MongoDB Explorer | Raw document viewer + 5 key aggregation queries |
| 📡 Bias Drift | Election-to-election comparison (like ML model versioning) |
| 🔍 Constituency Drill-Down | State + year deep dive, candidate profiles |
| 📄 Export Report | One-click PDF audit report with ReportLab |

---

## 🚀 Run Locally

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/india-election-bias-audit.git
cd india-election-bias-audit
```

### 2. Create virtual environment
```bash
py -3.11 -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure MongoDB

**Option A — Local MongoDB (recommended for development)**
```
MONGODB_URI=mongodb://localhost:27017/
```

**Option B — MongoDB Atlas**
```
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
```

Copy the example and fill in your URI:
```bash
cp .env.example .env
```

### 5. Run the app
```bash
streamlit run app.py
```

### 6. Seed the database
Click **🌱 Seed Database** in the sidebar — inserts 45,000+ records across 4 collections.

---

## 🧠 AI Fairness Framework

This project applies the same methodology used in production ML model monitoring:

- **Demographic Parity** — equal positive prediction rates across groups
- **Equal Opportunity** — equal true positive rates across groups  
- **Win-Rate Gap** — difference in winning probability between demographics
- **Drift Detection** — tracking bias improvement/regression across "versions" (elections)

The Bias Drift page lets you compare any two elections like ML model versions — showing which metrics improved, worsened, or stayed flat.

---

## 📁 Project Structure

```
india-election-bias-audit/
├── app.py                        ← Main dashboard (run this)
├── requirements.txt
├── .env.example
├── README.md
├── utils/
│   ├── data_generator.py         ← Generates realistic election data
│   └── db.py                     ← MongoDB connection + query helpers
└── pages/
    ├── 1_Gender_Bias.py
    ├── 2_Party_Scorecard.py
    ├── 3_Caste_Regional.py
    ├── 4_Alerts.py
    ├── 5_MongoDB_Explorer.py
    ├── 6_Bias_Drift.py
    ├── 7_Constituency_Drilldown.py
    └── 8_Export_Report.py
```

---

## 🗃️ Data Sources

Currently uses pattern-matched synthetic data based on real ECI statistics. For real data:

| Source | Link |
|---|---|
| ECI Statistical Reports | eci.gov.in/statistical-reports |
| Datameet India | github.com/datameet/india-election-data |
| data.gov.in | data.gov.in/catalog/general-election-lok-sabha-2024 |
| MyNeta | myneta.info |

---

## 🛠️ Tech Stack

- **Database** — MongoDB (Local / Atlas)
- **Backend** — Python 3.11 + PyMongo
- **Dashboard** — Streamlit
- **Charts** — Plotly
- **PDF Export** — ReportLab
- **Data** — Pandas + NumPy

---

## 📄 License

MIT License — free to use, modify and distribute.

---

<p align="center">Made with ❤️ for AI Fairness Research · College Project</p>
