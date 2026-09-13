# Project Architecture Rules (Plan Mode)

This file provides guidance to agents when working with code in this repository.

## Frozen Architecture — Do Not Redesign

The architecture has been approved by the team. Planning tasks must translate requirements into implementation detail, not propose alternative designs.

## Data Flow (must be preserved in any plan)

```
SensorData (CSV/SQLite)
  → Feature Engineering (data_processor.py)
  → Isolation Forest (anomaly_detection.py)  →  anomaly score + severity
  → Random Forest (predict.py)               →  failure probability + risk level
  → Evidence Engine (evidence_engine.py)     →  Evidence object (combined)
  → Readiness Engine (readiness_engine.py)   →  ReadinessResult (deterministic)
  → Maintenance Optimizer                    →  Ranked recommendations
  → FastAPI routes                           →  JSON responses
  → React frontend                           →  renders results only
  → IBM Bob via AssetSentinel MCP            →  explains pre-computed results
```

## Hidden Coupling Points

- The Evidence Layer is the single coupling point between ML outputs and all decision/explanation layers. If the Evidence schema changes, readiness engine, maintenance engine, MCP tools, and Bob prompts all need updating.
- Mission-specific readiness reuses the same Readiness Engine but with a different Evidence input (mission `required_components` and `criticality` change the `mission_impact` field in Evidence).
- The Readiness Engine must be called twice per asset when evaluating fleet readiness against multiple missions — plan for this in API design.

## Non-Negotiable Implementation Constraints

- Readiness weights and thresholds in ONE config object — both the Readiness Engine and any documentation must reference the same values
- SQLAlchemy models and Pydantic schemas are separate Python classes — do not merge them
- Bob MCP tools must call the same FastAPI endpoint logic (or shared service layer) as the regular API — never duplicate business logic for Bob

## Infrastructure Constraints (things to avoid in plans)

Do NOT plan for: Kafka, Airflow, PostgreSQL, TimescaleDB, MinIO, Feast, Spark, Celery, Redis, LSTM, Autoencoder, SHAP, full RAG, microservices

## Mission-Aware Readiness Architecture

Same physical asset, different readiness result depending on mission:
- Evidence is re-assembled with mission `required_components` and mission `criticality`
- `mission_impact` field in Evidence changes based on whether asset's at-risk component is required by mission
- Readiness Engine applies mission's own `readiness_threshold` (can override global threshold)
- Both generic and mission-specific results must be persisted to `ReadinessResults` table

## Database Schema — Required Tables

`Assets` | `Components` | `SensorData` | `MaintenanceRecords` | `Missions` | `Predictions` | `ReadinessResults` | `MaintenanceRecommendations`

## API Completeness Requirement

All 16 endpoints listed in the architecture spec must be implemented:
`GET /api/assets`, `/api/assets/{id}`, `/api/assets/{id}/sensors`, `/api/assets/{id}/health`,
`/api/assets/{id}/predictions`, `/api/assets/{id}/anomalies`, `/api/assets/{id}/maintenance`,
`/api/assets/{id}/readiness`, `/api/missions`, `/api/missions/{id}`, `/api/missions/{id}/readiness`,
`/api/maintenance/priorities`, `/api/fleet/readiness`, `POST /api/copilot/chat`
