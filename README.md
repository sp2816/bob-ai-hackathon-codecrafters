
# 🚀 AssetSentinel — Mission Readiness & Predictive Maintenance Copilot

## 👥 Team

| Field | Value |
|---|---|
| **Team Name** | Codecrafters |
| **Track** | AI |
| **Team Lead** | Tisha Soni — tis007.ts@gmail.com |
| **Members** | Selin Parmar, Mukt Patel, Dhruv Sutariya |

---

## 🎯 Problem Statement

What problem does your project solve? Who experiences this problem?

Military organisations cannot always accurately determine whether aircraft,
vehicles, and critical equipment are mission-ready. Valuable HUMS sensor data
and service records can remain underutilised, causing maintenance to be
reactive and failures to occur unexpectedly, reducing operational readiness.

---

## 💡 Solution

What did you build? How does it solve the problem above?

AssetSentinel analyses sensor data, asset usage patterns, and service
records to generate a dynamic mission-readiness score and identify assets that
require attention. The system predicts component failure risks, explains the
factors affecting readiness, and recommends a prioritised maintenance plan
based on mission impact and equipment health.

---

## ✨ Key Features

- **Dynamic Readiness Score:** Calculates a continuously updated readiness
  score for every asset based on component health and operational data.
- **Predictive Failure Analysis:** Detects risk patterns and identifies
  components likely to require maintenance before the next mission window.
- **Explainable Readiness Intelligence:** Shows why an asset is classified as
  ready, conditionally ready, or non-ready.
- **Mission-Aware Evaluation:** Evaluates the same asset differently based on
  the health requirements and criticality of a selected mission.
- **Readiness Engine:** Computes holistic operational status and mission capability.
- **Maintenance Priority:** Rank-orders maintenance actions based on ML risk and urgency.
- **IBM Copilot Integration:** See [IBM Bob Integration Docs](docs/ibm-bob-integration.md) for details on the IDE MCP Server and the real Watsonx.ai chat interface.

---

## 🛠️ Tech Stack

| Category | Technologies |
|---|---|
| **Languages** | Python, TypeScript, JavaScript |
| **Frameworks** | FastAPI, React |
| **IBM Technologies** | IBM Bob |
| **Databases** | SQLite |
| **Other** | Scikit-learn, Pandas, NumPy, SQLAlchemy, Joblib, Pytest, Git, GitHub |

---

## 📁 Repository Structure

```
├── src/                  # All source code
├── docs/                 # Written documentation
│   ├── problem-statement.md
│   ├── solution-overview.md
│   ├── architecture.md
│   └── setup-guide.md
├── demo/                 # Demo artifacts
│   ├── screenshots/      # App screenshots
│   └── demo-video-link.txt  # Link to demo video
├── presentation/         # Slide deck
└── submission.yaml       # Structured submission metadata
```

---

## ⚡ How to Run

> **Copy these exact steps from your [`docs/setup-guide.md`](docs/setup-guide.md)**

```bash
# 1. Clone the repo
git clone https://github.com/sp2816/bob-ai-hackathon-codecrafters.git
cd bob-ai-hackathon-codecrafters

# 2. Install dependencies
pip install -r src/backend/member1_backend/requirements.txt
pip install -r src/backend/member2_ml/requirements.txt
cd src/frontend
npm install

# 3. Configure environment
# Note: Core application does not require API keys, but if a .env.example exists:
cp .env.example .env

# 4. Run the backend (in terminal 1)
cd ../..
cd src/backend/member1_backend
uvicorn app.main:app --reload

# 5. Run the frontend (in terminal 2)
cd ../../../src/frontend
npm run dev
```

---

## 🖥️ Demo

| Artifact | Link |
|---|---|
| 📹 Demo Video | [See demo/demo-video-link.txt](demo/demo-video-link.txt) |
| 🌐 Live Demo | [See demo/live-demo-url.txt](demo/live-demo-url.txt) |
| 🖼️ Screenshots | [See demo/screenshots/](demo/screenshots/) |
| 📊 Presentation | [See presentation/slides.pdf](presentation/) |

---

## ⚠️ Known Limitations

> Be honest — judges appreciate transparency over overclaiming.

- The prototype uses simulated or available sensor and maintenance datasets.
- Predictions are intended for decision support and demonstration purposes.
- The prototype focuses on selected component health indicators.
---

## 🏅 What We're Most Proud Of

SentinelReady AI transforms raw maintenance and sensor information into
mission-aware, explainable decisions. Rather than simply predicting failure,
the system connects component health, mission requirements, and maintenance
priority to help users understand what action should be taken and why.

---
