# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Three Locked Decisions (from pre-implementation review)

1. **MCP transport**: Local IBM Bob → `.bob/mcp.json` (STDIO) → `src/backend/app/mcp/server.py` — genuine working integration, not docs-only
2. **RF probability**: AS-1047's failure probability emerges from real model inference — never hardcode `if asset_id == "AS-1047": probability = 0.87`
3. **Doc integrity**: Documentation must describe the ACTUAL implemented system — update docs at Phase 11 with real commands and real model outputs

## Project Identity

**AssetSentinel — Mission Readiness & Predictive Maintenance Copilot**
Team: Codecrafters | Track: AI | IBM Bob Hackathon submission

## Architecture — FROZEN (do not redesign)

```
Sensor Data → ML (Random Forest + Isolation Forest)
           → Evidence Layer
           → Readiness Engine (deterministic)     → Readiness Result
           → Maintenance Priority Engine          → Ranked Actions
           → IBM Bob (via AssetSentinel MCP)      → Explanation
```

**Core rule**: IBM Bob NEVER decides readiness. The deterministic Readiness Engine is the sole authority.  
**Core rule**: React NEVER calculates readiness/scores. It renders backend-computed results only.

## Repository Structure

```
src/
  backend/    Python / FastAPI / SQLite
  frontend/   React / TypeScript / Vite / Tailwind
docs/         Architecture docs (must update docs/architecture.md with Mermaid diagram)
demo/         Screenshots + video link (min 3 screenshots, real video URL required)
presentation/ slides.pdf or slides.pptx required
submission.yaml  Must fill ALL required fields before submission
```

## Critical Preservation Rules

- **Never delete or rename**: README.md, submission.yaml, docs/, demo/, presentation/, CONTRIBUTING.md, .github/workflows/validate.yml
- **submission.yaml validation**: GitHub Action checks for non-empty: title, problem_statement, solution_summary, key_features (≥3), tech_stack arrays, team info
- **README.md**: All `[placeholder]` text must be replaced before submission
- **demo/demo-video-link.txt**: Must not contain placeholder URL before submission
- **src/ must have ≥1 code file** for the GitHub Action to pass

## Backend Conventions

- **Never** bypass the Evidence Layer to pass raw sensor/ML data to Readiness Engine or Bob
- **Readiness weights/thresholds** live in one config location only (e.g. `backend/app/config.py`)
- Readiness score formula: `0.40×FailureRisk + 0.25×AnomalySeverity + 0.20×ComponentCriticality + 0.15×MissionImpact`
- Thresholds: 0.00–0.34 → READY | 0.35–0.66 → CONDITIONALLY READY | 0.67–1.00 → NOT READY
- Hard rules execute before score: overdue inspection on critical component → NOT READY immediately
- Use Pydantic schemas for API contracts; SQLAlchemy models for DB — keep them separate
- Canonical demo asset: **AS-1047** (87% bearing failure risk, HIGH vibration anomaly, overdue inspection)

## ML Rules

- **Isolation Forest**: detects anomalies vs asset's own historical baseline — outputs anomaly score/status/sensor/severity
- **Random Forest**: predicts failure probability 0–1 — outputs risk level (LOW/MEDIUM/HIGH) + at-risk component
- Do NOT generate RUL (remaining useful life) time predictions — RF is not an RUL model
- Do NOT use SHAP for MVP per-asset explanations — Evidence Layer items are the explanation
- Explainability comes from Evidence Layer evidence items, not model internals

## MCP Integration

- AssetSentinel exposes a read-only MCP server/interface for IBM Bob
- Bob calls MCP tools to retrieve pre-computed results: `get_asset_status`, `get_failure_predictions`, `get_mission_readiness`, etc.
- Bob then explains the already-computed Evidence + Readiness result — never overrides it
- MCP lives in `src/backend/app/mcp/` or similar — do not bake Bob prompts into business logic

## Technology Constraints

**Approved only**: React, TypeScript, Vite, Tailwind, Recharts, Axios | Python, FastAPI, SQLite, SQLAlchemy, Pydantic, Pandas, NumPy, scikit-learn  
**Prohibited**: Kafka, Airflow, PostgreSQL, TimescaleDB, MinIO, Feast, Spark, Celery, Redis, LSTM, Autoencoder

## Environment Variables

Copy from `src/.env.example`. Backend uses `WATSONX_API_KEY`, `WATSONX_PROJECT_ID`, `WATSONX_URL`, `DATABASE_URL`, `APP_PORT=8000`. Never commit actual secrets.

## Commands (to be finalized once code is written)

```bash
# Backend
cd src/backend && pip install -r requirements.txt
cd src/backend && uvicorn app.main:app --reload --port 8000

# Frontend
cd src/frontend && npm install
cd src/frontend && npm run dev

# Tests (backend)
cd src/backend && pytest tests/
cd src/backend && pytest tests/test_readiness_engine.py   # single test file

# Tests (frontend)
cd src/frontend && npm test
```
