# Project Coding Rules (Agent Mode)

This file provides guidance to agents when working with code in this repository.

## File Ownership — Never Cross These Boundaries

| Member | Owns exclusively |
|---|---|
| Member 1 | `main.py`, `database.py`, `config.py`, `db/models.py`, `schemas/asset.py`, `schemas/sensor.py`, `schemas/mission.py`, `routers/assets.py`, `routers/missions.py`, `routers/fleet.py`, `routers/maintenance_records.py`, `scripts/seed_db.py` |
| Member 2 | `ml/`, `data/`, `services/data_processor.py`, `services/prediction_engine.py`, `schemas/prediction.py`, `routers/ml.py` |
| Member 3 | `services/evidence_engine.py`, `services/readiness_engine.py`, `services/maintenance_optimizer.py`, `services/watsonx_service.py`, `schemas/readiness.py`, `schemas/maintenance.py`, `schemas/copilot.py`, `routers/maintenance_plan.py`, `routers/copilot.py`, `mcp/server.py` |
| Member 4 | All of `frontend/` |

## Router Separation Rules

- `routers/ml.py` — Member 2 owns this; contains ONLY `/predictions` and `/anomalies` endpoints
- `routers/maintenance_records.py` — Member 1; maintenance upload and history
- `routers/maintenance_plan.py` — Member 3; recommendations and priorities
- Member 2 NEVER edits `routers/assets.py`
- `config.py` changes require Member 1 to merge as PR to avoid conflicts

## Strict Architectural Constraints

- Evidence Layer is MANDATORY between ML outputs and all downstream consumers (Readiness Engine, Maintenance Engine, Bob). Never short-circuit it.
- Readiness Engine is deterministic — hard rules first, then weighted score. Never add ML inference inside the engine.
- React components MUST NOT contain any readiness scoring logic. All `readiness_status`, `readiness_score`, `reasons`, and `evidence` come from backend API responses.
- MCP tools are read-only — never add write/mutation operations to the AssetSentinel MCP server.

## Module Responsibilities (do not drift)

| Module | Does | Does NOT |
|---|---|---|
| `evidence_engine.py` | Assembles Evidence object from ML + maintenance + mission data | Calculate readiness |
| `readiness_engine.py` | Applies hard rules + weighted formula to Evidence | Run ML inference |
| `maintenance_optimizer.py` | Ranks actions using `w1×FailureRisk + w2×Criticality + w3×MissionImpact + w4×Urgency` | Fetch raw sensor data |
| `prediction_engine.py` | Calls Isolation Forest + Random Forest models | Make readiness decisions |
| MCP server | Retrieves pre-computed results for Bob | Compute anything from scratch |
| `watsonx_service.py` | Manages IBM Bob API calls and system prompt | Make readiness decisions |

## Config Centralization

- All readiness weights and thresholds must live in one place only: `src/backend/app/config.py`
- Member 3 reads constants from config; Member 1 owns the file; changes go through Member 1 as PR
- Never hardcode `0.40`, `0.25`, `0.20`, `0.15`, or `0.34`/`0.66` threshold values in engine files

## Database Rules

- Use SQLAlchemy ORM models in `db/models.py` — never raw SQL strings in route handlers
- Use Pydantic schemas in `schemas/` for all API input/output validation — never return SQLAlchemy model objects directly from API endpoints
- `routers/` directory is named `routers/` not `api/` — do not create an `api/` directory

## Mock Layer (Frontend)

- `VITE_USE_MOCK=true` in `.env.local` → `api.ts` returns `mockData.ts` fixture data
- Switch to `VITE_USE_MOCK=false` at Milestone B when real backend is ready
- `mockData.ts` must match API contract shapes exactly — update it when schemas change

## Testing

- Backend tests use `pytest` in `src/backend/tests/`
- Member 3's unit tests run WITHOUT a DB connection (pure functions)
- Run single test file: `cd src/backend && pytest tests/test_<name>.py -v`
- Run single test function: `cd src/backend && pytest tests/test_<name>.py::test_function_name -v`
- Frontend tests: `cd src/frontend && npm test`

## Data Integrity

- Canonical demo scenario (AS-1047) must remain consistent across all layers:
  - Vibration anomaly → HIGH severity
  - Bearing failure risk → ~0.87 (HIGH) — actual value from model, document whatever it is
  - Inspection status → OVERDUE (420h since last service)
  - MSN-003 → NOT READY (hard rule fires)
  - MSN-001 → CONDITIONALLY READY
  - Maintenance rank → #1 bearing inspection/replacement

## MSN-003 Components (stealth removed)
- Required: `engine`, `sensors`, `avionics`, `communications`
- NOT: stealth systems

## Submission Validation (GitHub Action checks these)

- `submission.yaml`: title, problem_statement, solution_summary, tech_stack arrays, key_features (≥3) must all be non-empty
- `demo/demo-video-link.txt`: must not contain placeholder text before final submission
- `demo/screenshots/`: needs ≥3 PNG/JPG files named `01-*.png`, `02-*.png`, `03-*.png`
- `presentation/`: needs `slides.pdf` or `slides.pptx`
