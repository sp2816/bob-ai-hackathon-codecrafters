# Project Documentation Context (Ask Mode)

This file provides guidance to agents when working with code in this repository.

## What This Project Is

AssetSentinel is a **predictive maintenance and mission-readiness decision-support** system for fleet assets (military/industrial). It is a hackathon prototype — synthetic data only, no real operational use claimed.

## Key Counterintuitive Facts

- **IBM Bob does NOT decide readiness** — this is the #1 architectural rule. Bob only explains pre-computed results from the deterministic Readiness Engine.
- **Two separate readiness calculations exist for the same asset**: generic readiness (no mission context) and mission-specific readiness. Same asset, same sensor data, different result depending on mission criticality and required components.
- **Evidence Layer is a first-class component**, not a helper. All downstream decision components (Readiness, Maintenance, Bob) consume Evidence objects — never raw ML outputs.
- **Random Forest predicts failure probability, NOT remaining useful life** — do not describe it as an RUL model.
- **Isolation Forest compares against the asset's own historical baseline**, not fleet-wide norms.

## Documentation Map

| File | Purpose |
|---|---|
| `docs/architecture.md` | Primary architecture doc + Mermaid diagram (team must fill) |
| `docs/solution-overview.md` | Template guidance only until team fills it |
| `docs/problem-statement.md` | Template guidance only until team fills it |
| `docs/setup-guide.md` | Evaluated by automated pipeline — must have real commands |
| `docs/template-guide.md` | Meta-guide explaining the hackathon template (do not modify) |
| `CONTRIBUTING.md` | Submission workflow guide (do not modify) |

## Evaluation Scoring

From the hackathon rubric (100 points total):
- Technical Implementation: 25 pts
- Innovation & Differentiation: 25 pts  
- Problem Depth & Vision: 15 pts
- Working Demo & Functionality: 15 pts
- **IBM Bob Integration: 10 pts** (explicitly scored — Bob must be genuinely useful)
- Documentation & Reproducibility: 10 pts

## MCP Integration Context

The AssetSentinel MCP server bridges IBM Bob to the backend. It exposes read-only tools named:
`get_asset_status`, `get_asset_details`, `get_sensor_trends`, `get_component_health`,
`get_failure_predictions`, `get_anomalies`, `get_maintenance_history`,
`get_mission_readiness`, `get_fleet_readiness`, `get_maintenance_priorities`, `get_mission_details`

These tools call the FastAPI backend internally and return structured data for Bob to explain.
