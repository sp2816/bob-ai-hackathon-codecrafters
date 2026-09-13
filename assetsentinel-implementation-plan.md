# AssetSentinel — Final Implementation Plan

**Team**: Codecrafters | **Track**: AI | **IBM Bob Hackathon**
**Product**: AssetSentinel — Mission Readiness & Predictive Maintenance Copilot

> Architecture is FROZEN. This plan incorporates all three explicit decisions and the parallel team structure.
> Do not redesign. The 15 implementation principles from the pre-implementation review remain active.

---

## Three Locked Decisions

| # | Decision | Rule |
|---|---|---|
| 1 | **MCP transport** | Local IBM Bob → `.bob/mcp.json` (STDIO) → `src/backend/app/mcp/server.py` — genuine working integration |
| 2 | **RF probability** | AS-1047 failure probability emerges from real model inference — never hardcode per asset |
| 3 | **Doc integrity** | Phase 0 drafts docs; Phase 11 finalises with actual commands, real model outputs, real demo values |

---

## Team Roles

| Member | Primary Domain |
|---|---|
| **Member 1** | Backend infrastructure, API contracts, shared schemas, assets/missions/readiness/fleet routes, maintenance records routes |
| **Member 2** | ML pipeline, synthetic data, training, anomaly detection, failure prediction, ML API routes |
| **Member 3** | Decision engines (Evidence, Readiness, Maintenance), watsonx/Bob backend, Copilot API, maintenance plan routes |
| **Member 4** | React frontend, all UI pages, Copilot chat UI, mock data layer |

---

## A. Final Folder Structure

```
bob-ai-hackathon-codecrafters/             ← repo root — preserve all template files
├── AGENTS.md                               ← ✅ created
├── CONTRIBUTING.md                         ← preserve, do not modify
├── README.md                               ← fill Phase 0, finalise Phase 11
├── submission.yaml                         ← fill Phase 0
├── assetsentinel-implementation-plan.md    ← this file
├── .bob/
│   ├── mcp.json                            ← Phase 10 — STDIO MCP registration
│   ├── rules-agent/AGENTS.md               ← ✅ created
│   ├── rules-ask/AGENTS.md                 ← ✅ created
│   └── rules-plan/AGENTS.md                ← ✅ created
├── .github/
│   └── workflows/validate.yml              ← preserve, do not modify
├── docs/
│   ├── architecture.md                     ← ✅ created
│   ├── problem-statement.md                ← fill Phase 0
│   ├── setup-guide.md                      ← draft Phase 0, finalise Phase 11
│   ├── solution-overview.md                ← fill Phase 0
│   └── template-guide.md                   ← preserve, do not modify
├── demo/
│   ├── demo-video-link.txt                 ← update Phase 11
│   ├── live-demo-url.txt                   ← update Phase 11
│   └── screenshots/                        ← add ≥3 images Phase 11
├── presentation/
│   └── slides.pdf                          ← Phase 11
└── src/
    ├── .env.example                         ← update Phase 1
    ├── README.md                            ← preserve
    ├── backend/
    │   ├── requirements.txt                 ← Member 1
    │   ├── .env.example                     ← Member 1
    │   └── app/
    │       ├── main.py                      ← Member 1 (router registration, startup)
    │       ├── database.py                  ← Member 1
    │       ├── config.py                    ← Member 1 (all weights/thresholds)
    │       ├── db/
    │       │   └── models.py                ← Member 1
    │       ├── schemas/
    │       │   ├── asset.py                 ← Member 1
    │       │   ├── sensor.py                ← Member 1
    │       │   ├── mission.py               ← Member 1
    │       │   ├── readiness.py             ← Member 3
    │       │   ├── maintenance.py           ← Member 3
    │       │   ├── prediction.py            ← Member 2
    │       │   └── copilot.py               ← Member 3
    │       ├── routers/
    │       │   ├── assets.py                ← Member 1 (asset CRUD + sensor + readiness)
    │       │   ├── missions.py              ← Member 1 (mission CRUD + mission readiness)
    │       │   ├── fleet.py                 ← Member 1 (fleet readiness summary)
    │       │   ├── maintenance_records.py   ← Member 1 (upload, history)
    │       │   ├── ml.py                    ← Member 2 (predictions + anomalies endpoints)
    │       │   ├── maintenance_plan.py      ← Member 3 (recommendations + priorities)
    │       │   └── copilot.py               ← Member 3 (POST /api/copilot/chat)
    │       ├── services/
    │       │   ├── evidence_engine.py       ← Member 3
    │       │   ├── readiness_engine.py      ← Member 3
    │       │   ├── maintenance_optimizer.py ← Member 3
    │       │   ├── watsonx_service.py       ← Member 3
    │       │   ├── prediction_engine.py     ← Member 2
    │       │   └── data_processor.py        ← Member 2
    │       ├── ml/
    │       │   ├── train_model.py           ← Member 2
    │       │   ├── predict.py               ← Member 2
    │       │   ├── anomaly_detection.py     ← Member 2
    │       │   └── models/
    │       │       ├── random_forest.pkl    ← Member 2 (generated)
    │       │       └── isolation_forest.pkl ← Member 2 (generated)
    │       ├── data/
    │       │   ├── assets.csv               ← Member 2
    │       │   ├── components.csv           ← Member 2
    │       │   ├── sensor_data.csv          ← Member 2
    │       │   ├── maintenance_records.csv  ← Member 2
    │       │   └── missions.csv             ← Member 2
    │       ├── scripts/
    │       │   └── seed_db.py               ← Member 1
    │       ├── mcp/
    │       │   └── server.py                ← Member 3
    │       └── tests/
    │           ├── test_evidence_engine.py  ← Member 3
    │           ├── test_readiness_engine.py ← Member 3
    │           ├── test_maintenance_optimizer.py ← Member 3
    │           ├── test_ml_pipeline.py      ← Member 2
    │           ├── test_api_assets.py       ← Member 1
    │           └── test_api_readiness.py    ← Member 1
    └── frontend/
        ├── package.json                     ← Member 4
        ├── vite.config.ts                   ← Member 4
        ├── tailwind.config.ts               ← Member 4
        ├── tsconfig.json                    ← Member 4
        ├── index.html                       ← Member 4
        └── src/
            ├── App.tsx                      ← Member 4
            ├── main.tsx                     ← Member 4
            ├── mocks/
            │   ├── handlers.ts              ← Member 4 (MSW mock handlers)
            │   └── mockData.ts              ← Member 4 (realistic AS-1047 fixture data)
            ├── services/
            │   └── api.ts                   ← Member 4
            ├── types/
            │   └── index.ts                 ← Member 4 (mirrors backend schemas)
            ├── components/
            │   ├── layout/
            │   │   ├── Sidebar.tsx          ← Member 4
            │   │   └── Layout.tsx           ← Member 4
            │   ├── charts/
            │   │   ├── SensorChart.tsx      ← Member 4
            │   │   └── RiskGauge.tsx        ← Member 4
            │   ├── assets/
            │   │   ├── AssetCard.tsx        ← Member 4
            │   │   └── AssetStatusBadge.tsx ← Member 4
            │   ├── maintenance/
            │   │   └── PriorityRow.tsx      ← Member 4
            │   ├── missions/
            │   │   └── MissionReadinessCard.tsx ← Member 4
            │   └── copilot/
            │       ├── ChatMessage.tsx      ← Member 4
            │       └── ChatInput.tsx        ← Member 4
            └── pages/
                ├── Dashboard.tsx            ← Member 4
                ├── Assets.tsx               ← Member 4
                ├── AssetDetails.tsx         ← Member 4
                ├── Predictions.tsx          ← Member 4
                ├── MaintenancePlan.tsx      ← Member 4
                ├── Missions.tsx             ← Member 4
                └── Copilot.tsx              ← Member 4
```

---

## B. Exact File Ownership

### Member 1 — Backend Infrastructure & Core Routes

| File | Responsibility |
|---|---|
| `app/main.py` | FastAPI app factory, CORS, startup, router registration |
| `app/database.py` | SQLAlchemy engine, `SessionLocal`, `Base` |
| `app/config.py` | ALL weights and thresholds — single source of truth |
| `app/db/models.py` | All 8 SQLAlchemy ORM models |
| `app/schemas/asset.py` | `AssetOut`, `AssetListOut`, `SensorDataOut` |
| `app/schemas/sensor.py` | `SensorTrendsOut` |
| `app/schemas/mission.py` | `MissionOut`, `MissionListOut` |
| `app/scripts/seed_db.py` | DB seeding from CSV files |
| `app/routers/assets.py` | `GET /api/assets`, `/api/assets/{id}`, `/sensors`, `/health`, `/readiness` |
| `app/routers/missions.py` | `GET /api/missions`, `/api/missions/{id}`, `/api/missions/{id}/readiness` |
| `app/routers/fleet.py` | `GET /api/fleet/readiness` |
| `app/routers/maintenance_records.py` | `GET /api/assets/{id}/maintenance`, `POST /api/assets/{id}/maintenance` |
| `requirements.txt` | Backend dependencies |
| `tests/test_api_assets.py` | Asset and mission API integration tests |
| `tests/test_api_readiness.py` | Readiness endpoint integration tests |

**Member 1 publishes the API contract on Day 1** so all other members can work in parallel.

### Member 2 — ML Pipeline & ML Routes

| File | Responsibility |
|---|---|
| `data/assets.csv` | 10-asset synthetic dataset |
| `data/components.csv` | Components with criticality and service intervals |
| `data/sensor_data.csv` | Time-series readings; AS-1047 intentionally anomalous |
| `data/maintenance_records.csv` | Service history; AS-1047 bearing 420h overdue |
| `data/missions.csv` | 3 missions with required components |
| `app/services/data_processor.py` | Feature engineering (rolling stats, z-score, trend, overdue flag) |
| `app/ml/train_model.py` | Training script for both models |
| `app/ml/predict.py` | Random Forest inference |
| `app/ml/anomaly_detection.py` | Isolation Forest inference |
| `app/ml/models/*.pkl` | Trained model artifacts (committed) |
| `app/services/prediction_engine.py` | Orchestrates inference, stores Prediction records |
| `app/schemas/prediction.py` | `PredictionOut`, `AnomalyOut` |
| `app/routers/ml.py` | `GET /api/assets/{id}/predictions`, `GET /api/assets/{id}/anomalies` |
| `tests/test_ml_pipeline.py` | ML inference correctness and model output tests |

**Member 2 never edits `routers/assets.py`** — ML endpoints live entirely in `routers/ml.py`.

### Member 3 — Decision Engines, watsonx/Bob Backend, Maintenance Plan Routes

| File | Responsibility |
|---|---|
| `app/services/evidence_engine.py` | `assemble_evidence()` — combines ML + maintenance + mission data |
| `app/services/readiness_engine.py` | `compute_readiness()` — hard rules + weighted score |
| `app/services/maintenance_optimizer.py` | `rank_all_assets()` — ranked fleet maintenance plan |
| `app/services/watsonx_service.py` | IBM Bob / watsonx API calls, system prompt management |
| `app/schemas/readiness.py` | `EvidenceOut`, `ReadinessResultOut` |
| `app/schemas/maintenance.py` | `MaintenanceRecommendationOut`, `MaintenancePriorityOut` |
| `app/schemas/copilot.py` | `CopilotChatIn`, `CopilotChatOut` |
| `app/routers/maintenance_plan.py` | `GET /api/maintenance/priorities` |
| `app/routers/copilot.py` | `POST /api/copilot/chat` |
| `app/mcp/server.py` | AssetSentinel MCP server (STDIO, 11 read-only tools) |
| `tests/test_evidence_engine.py` | Evidence assembly unit tests |
| `tests/test_readiness_engine.py` | Hard rules + weighted score unit tests |
| `tests/test_maintenance_optimizer.py` | Priority ranking unit tests |

**Member 3 writes pure functions first** (database-independent, fully unit-testable), then wires to DB.

### Member 4 — React Frontend (all of it)

| File / Directory | Responsibility |
|---|---|
| `frontend/src/mocks/mockData.ts` | Realistic AS-1047 fixture data matching API contract |
| `frontend/src/mocks/handlers.ts` | MSW (Mock Service Worker) or env-flag mock handlers |
| `frontend/src/services/api.ts` | Axios client; `USE_MOCK` env flag switches to mock data |
| `frontend/src/types/index.ts` | TypeScript interfaces matching backend Pydantic schemas |
| All `components/**` | Layout, charts, asset, maintenance, mission, copilot components |
| All `pages/**` | All 7 pages |

**Member 4 uses `USE_MOCK=true`** against realistic mock data from Day 1. Frontend is never blocked by backend progress.

---

## C. Final API Endpoints

### Member 1 — Assets, Missions, Fleet, Maintenance Records

| Method | Path | Router File | Description |
|---|---|---|---|
| `GET` | `/api/assets` | `routers/assets.py` | List all assets |
| `GET` | `/api/assets/{asset_id}` | `routers/assets.py` | Asset detail + latest prediction summary |
| `GET` | `/api/assets/{asset_id}/sensors` | `routers/assets.py` | Sensor time-series (last N readings) |
| `GET` | `/api/assets/{asset_id}/health` | `routers/assets.py` | Current overall health from latest Prediction |
| `GET` | `/api/assets/{asset_id}/readiness` | `routers/assets.py` | Generic readiness (no mission context) |
| `GET` | `/api/missions` | `routers/missions.py` | List all missions |
| `GET` | `/api/missions/{mission_id}` | `routers/missions.py` | Mission detail |
| `GET` | `/api/missions/{mission_id}/readiness` | `routers/missions.py` | Per-asset readiness for this mission |
| `GET` | `/api/fleet/readiness` | `routers/fleet.py` | Fleet-wide readiness summary |
| `GET` | `/api/assets/{asset_id}/maintenance` | `routers/maintenance_records.py` | Maintenance history for asset |
| `POST` | `/api/assets/{asset_id}/maintenance` | `routers/maintenance_records.py` | Upload new maintenance record |

### Member 2 — ML Predictions & Anomalies

| Method | Path | Router File | Description |
|---|---|---|---|
| `GET` | `/api/assets/{asset_id}/predictions` | `routers/ml.py` | Latest failure prediction (Random Forest) |
| `GET` | `/api/assets/{asset_id}/anomalies` | `routers/ml.py` | Latest anomaly detection (Isolation Forest) |

### Member 3 — Maintenance Plan & Copilot

| Method | Path | Router File | Description |
|---|---|---|---|
| `GET` | `/api/maintenance/priorities` | `routers/maintenance_plan.py` | Fleet-wide ranked maintenance plan |
| `POST` | `/api/copilot/chat` | `routers/copilot.py` | IBM Bob chat with Evidence context |

**Total: 14 primary endpoints + 1 upload endpoint = 15 endpoints**

---

## D. API Contract (Published Day 1 by Member 1)

Member 1 publishes this contract before any parallel work begins. All members write code against these shapes.

### `GET /api/assets`
```json
[
  {
    "id": "AS-1047",
    "name": "Rotary Wing Asset 1047",
    "type": "Rotary Wing",
    "status": "DEGRADED",
    "location": "Base Alpha",
    "total_flight_hours": 1420.5,
    "latest_risk_level": "HIGH",
    "latest_readiness_status": "NOT_READY"
  }
]
```

### `GET /api/assets/{asset_id}`
```json
{
  "id": "AS-1047",
  "name": "Rotary Wing Asset 1047",
  "type": "Rotary Wing",
  "status": "DEGRADED",
  "location": "Base Alpha",
  "commission_date": "2018-03-15",
  "total_flight_hours": 1420.5
}
```

### `GET /api/assets/{asset_id}/sensors`
```json
{
  "asset_id": "AS-1047",
  "readings": [
    {"timestamp": "2024-01-15T10:00:00Z", "sensor_type": "vibration", "value": 4.2, "unit": "mm/s"},
    {"timestamp": "2024-01-15T10:15:00Z", "sensor_type": "vibration", "value": 4.8, "unit": "mm/s"}
  ],
  "anomalous_sensors": ["vibration"]
}
```

### `GET /api/assets/{asset_id}/predictions`
```json
{
  "asset_id": "AS-1047",
  "component": "main_bearing",
  "failure_probability": 0.87,
  "risk_level": "HIGH",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### `GET /api/assets/{asset_id}/anomalies`
```json
{
  "asset_id": "AS-1047",
  "anomaly_score": -0.52,
  "anomaly_status": "ANOMALOUS",
  "sensor": "vibration",
  "severity": "HIGH",
  "detected_at": "2024-01-15T10:30:00Z"
}
```

### `GET /api/assets/{asset_id}/readiness`
```json
{
  "asset_id": "AS-1047",
  "mission_id": null,
  "status": "CONDITIONALLY_READY",
  "score": 0.62,
  "reasons": [
    "Main bearing failure risk is HIGH (0.87)",
    "Vibration anomaly severity: HIGH"
  ],
  "evidence": {
    "asset_id": "AS-1047",
    "component": "main_bearing",
    "failure_risk": 0.87,
    "risk_level": "HIGH",
    "anomaly": {"sensor": "vibration", "severity": "HIGH", "score": -0.52},
    "maintenance": {"hours_since_service": 420.0, "inspection_status": "OVERDUE"},
    "criticality": "HIGH",
    "mission_impact": "NONE"
  },
  "computed_at": "2024-01-15T10:30:00Z"
}
```

### `GET /api/missions/{mission_id}/readiness`
```json
{
  "mission_id": "MSN-003",
  "mission_name": "High-Criticality Strike",
  "assets": [
    {
      "asset_id": "AS-1047",
      "status": "NOT_READY",
      "score": 0.87,
      "reasons": [
        "Mandatory inspection overdue on HIGH criticality component (main_bearing)",
        "main_bearing required for this mission"
      ],
      "evidence": { "...": "..." }
    }
  ]
}
```

### `GET /api/fleet/readiness`
```json
{
  "total": 10,
  "ready": 6,
  "conditionally_ready": 3,
  "not_ready": 1,
  "not_ready_assets": ["AS-1047"],
  "summary_at": "2024-01-15T10:30:00Z"
}
```

### `GET /api/maintenance/priorities`
```json
{
  "generated_at": "2024-01-15T10:30:00Z",
  "priorities": [
    {
      "rank": 1,
      "asset_id": "AS-1047",
      "component": "main_bearing",
      "action": "Inspect and replace main bearing on AS-1047",
      "priority_score": 0.91,
      "urgency": 0.88,
      "factors": {
        "failure_risk": 0.87,
        "criticality": "HIGH",
        "mission_impact": "HIGH",
        "urgency": 0.88
      }
    }
  ]
}
```

### `POST /api/copilot/chat`
**Request:**
```json
{
  "message": "Why is AS-1047 not mission-ready and what should we fix first?",
  "asset_id": "AS-1047",
  "mission_id": "MSN-003"
}
```
**Response:**
```json
{
  "response": "The Readiness Engine has determined AS-1047 is NOT READY for Mission MSN-003. Evidence: ...",
  "evidence_used": ["failure_probability: 0.87", "inspection_status: OVERDUE", "severity: HIGH"],
  "tools_called": ["get_mission_readiness", "get_failure_predictions", "get_maintenance_priorities"]
}
```

---

## E. Parallel Day 1 Tasks

All four members begin work simultaneously on Day 1 after Member 1 publishes the API contract.

### Member 1 — Day 1
1. Publish API contract (shapes above) in a shared doc or `docs/api-contract.md`
2. Create `src/backend/app/main.py`, `database.py`, `config.py`
3. Create `src/backend/app/db/models.py` (all 8 models)
4. Create `src/backend/app/schemas/asset.py`, `sensor.py`, `mission.py`
5. Create `src/backend/requirements.txt`
6. Create stub routers (`assets.py`, `missions.py`, `fleet.py`, `maintenance_records.py`) returning `{"status": "not_implemented"}` so the app starts and routes are registered
7. Push to `feature/backend-infrastructure`

### Member 2 — Day 1
1. Create all 5 CSV files in `data/` with the AS-1047 canonical scenario baked in
2. Create `app/services/data_processor.py` (feature engineering)
3. Begin `app/ml/train_model.py` skeleton
4. Create `app/schemas/prediction.py`
5. Push to `feature/ml-pipeline`

### Member 3 — Day 1
1. Create pure-function versions of `evidence_engine.py`, `readiness_engine.py`, `maintenance_optimizer.py` — **no database dependency** — accept plain dicts or Pydantic models as input
2. Write unit tests immediately: `test_evidence_engine.py`, `test_readiness_engine.py`, `test_maintenance_optimizer.py`
3. Create `app/schemas/readiness.py`, `maintenance.py`, `copilot.py`
4. Push to `feature/decision-engines`

### Member 4 — Day 1
1. Scaffold Vite + React + TypeScript + Tailwind project in `src/frontend/`
2. Create `src/types/index.ts` from the Day 1 API contract
3. Create `src/mocks/mockData.ts` with realistic AS-1047 fixture data matching contract shapes
4. Set `USE_MOCK=true` in `.env.local`; wire `api.ts` to return mock data when flag is set
5. Build `Layout.tsx`, `Sidebar.tsx`, `AssetStatusBadge.tsx`
6. Start `Dashboard.tsx` and `Assets.tsx` pages against mock data
7. Push to `feature/frontend`

---

## F. Integration Milestones

### Milestone A — Backend Core Runs (Member 1 + 2, ~Day 2)
- `uvicorn app.main:app` starts without errors
- `/api/assets` returns seeded asset list (DB populated)
- `/api/assets/AS-1047/predictions` returns ML prediction (models trained, `prediction_engine` wired to DB)
- **Unblocks Member 3**: can now wire services to real DB session instead of plain dicts

### Milestone B — Decision Engines Wired (Member 3, ~Day 3)
- `GET /api/assets/AS-1047/readiness` returns deterministic result with `reasons`
- `GET /api/maintenance/priorities` returns ranked list with AS-1047 at rank #1
- `GET /api/missions/MSN-003/readiness` returns NOT_READY for AS-1047
- `GET /api/missions/MSN-001/readiness` returns CONDITIONALLY_READY for AS-1047
- All three decision engine unit tests pass
- **Unblocks Member 4**: can switch `USE_MOCK=false` and connect to real backend

### Milestone C — Frontend Connected to Real Backend (Member 4, ~Day 4)
- All 7 pages render real backend data
- `USE_MOCK=false`; Vite proxy routes `/api` to `localhost:8000`
- Sensor trend chart on AssetDetails shows AS-1047 vibration deviation
- Readiness panel shows NOT_READY / CONDITIONALLY_READY correctly (no React computation)
- Copilot page sends to `POST /api/copilot/chat` and renders response

### Milestone D — IBM Bob MCP Live (Member 3, ~Day 4–5)
- `.bob/mcp.json` registered; `mcp/server.py` running via STDIO
- Bob calls `get_mission_readiness("AS-1047", "MSN-003")` and returns grounded result
- Bob calls `get_maintenance_priorities()` and cites rank #1 action
- Canonical interaction verified: "Why is AS-1047 not mission-ready?" → full explanation from retrieved data

---

## G. Database Schema

All models use `Base = declarative_base()`. SQLite file: `./assetsentinel.db`.

```
Asset
  id: str (PK, e.g. "AS-1047")
  name: str
  type: str                          (Rotary Wing / Fixed Wing / Ground Vehicle)
  status: str                        (OPERATIONAL / DEGRADED / GROUNDED)
  location: str
  commission_date: date
  total_flight_hours: float

Component
  id: str (PK, e.g. "COMP-AS1047-BEARING")
  asset_id: str (FK → Asset.id)
  name: str                          (main_bearing / engine / hydraulics / avionics / sensors / communications)
  type: str
  criticality: str                   (LOW / MEDIUM / HIGH)
  status: str                        (FUNCTIONAL / DEGRADED / NON_FUNCTIONAL)
  last_service_date: date
  service_interval_hours: float
  hours_at_last_service: float       ← enables hours_since_service computation

SensorData
  id: int (PK, autoincrement)
  asset_id: str (FK → Asset.id)
  timestamp: datetime
  sensor_type: str                   (vibration / temperature / pressure / rpm / oil_pressure)
  value: float
  unit: str

MaintenanceRecord
  id: int (PK, autoincrement)
  asset_id: str (FK → Asset.id)
  component_id: str (FK → Component.id)
  date: date
  type: str                          (INSPECTION / REPLACEMENT / OVERHAUL / REPAIR)
  technician: str
  notes: str
  hours_at_service: float

Mission
  id: str (PK, e.g. "MSN-001")
  name: str
  criticality: str                   (LOW / MEDIUM / HIGH)
  required_components: str           ← JSON list e.g. '["main_bearing","engine"]'
  readiness_threshold: float         ← mission override; NULL = use global READY_MAX
  scheduled_date: date

Prediction
  id: int (PK, autoincrement)
  asset_id: str (FK → Asset.id)
  component_id: str (FK → Component.id, nullable)
  failure_probability: float         (0.0–1.0 from Random Forest)
  risk_level: str                    (LOW / MEDIUM / HIGH)
  anomaly_score: float
  anomaly_status: str                (NORMAL / ANOMALOUS)
  anomaly_sensor: str
  anomaly_severity: str              (NONE / LOW / MEDIUM / HIGH)
  created_at: datetime

ReadinessResult
  id: int (PK, autoincrement)
  asset_id: str (FK → Asset.id)
  mission_id: str (FK → Mission.id, nullable — NULL = generic)
  status: str                        (READY / CONDITIONALLY_READY / NOT_READY)
  score: float
  reasons: str                       ← JSON list of reason strings
  evidence: str                      ← JSON-encoded EvidenceObject
  computed_at: datetime

MaintenanceRecommendation
  id: int (PK, autoincrement)
  asset_id: str (FK → Asset.id)
  component_id: str (FK → Component.id)
  priority_score: float
  action: str                        (human-readable)
  urgency: float                     (0.0–1.0)
  factors: str                       ← JSON dict {failure_risk, criticality, mission_impact, urgency}
  created_at: datetime
```

**Schema rules**:
- `required_components` and `reasons` are JSON strings — parsed in service layer, never in ORM models
- `mission_id = NULL` on `ReadinessResult` means generic (no mission context)
- SQLAlchemy models never returned directly from API — always converted via Pydantic schemas

---

## H. ML Implementation

### Synthetic Data Design (Member 2)

**AS-1047 canonical scenario**:
- Vibration readings: start at per-asset baseline, increase linearly from reading 150 onwards, reaching 3.5–4.0 σ above baseline by the final reading
- Temperature: mild upward trend correlated with vibration (bearing heat signature)
- Pressure, RPM: within normal range (fault is isolated to bearing)
- `hours_at_last_service` set so `hours_since_service = 420` and `service_interval_hours = 300` → OVERDUE

**Other 9 assets**: readings within ±1.5 σ of their individual baselines; bearings current.

**Component criticality map**:
- `main_bearing` → HIGH
- `engine` → HIGH
- `hydraulics` → MEDIUM
- `sensors` → MEDIUM
- `avionics` → MEDIUM
- `communications` → LOW

### Feature Engineering (`data_processor.py`)
Per-asset, per-sensor rolling window (size = 20):
- `rolling_mean`, `rolling_std`
- `z_score = (value − rolling_mean) / rolling_std`
- `max_z_score_24h` — peak z-score in last 24h window
- `vibration_trend` — linear slope of vibration over last 20 readings
- `hours_since_service` — `asset.total_flight_hours − component.hours_at_last_service`
- `overdue_flag` — 1 if `hours_since_service > service_interval_hours`, else 0
- `criticality_encoded` — LOW=0.33, MEDIUM=0.67, HIGH=1.0

### Isolation Forest
```python
IsolationForest(n_estimators=100, contamination=0.08, random_state=42)
```
Severity mapping: score < −0.3 → HIGH | −0.3 to −0.1 → MEDIUM | > −0.1 → NORMAL

### Random Forest
```python
RandomForestClassifier(n_estimators=200, max_depth=8, min_samples_leaf=2,
                       class_weight="balanced", random_state=42)
```
Training label rule: `failure = 1 if (z_score > 3.0 AND overdue_flag == 1 AND criticality == HIGH)`

Tuning path if AS-1047 output < 0.75: increase vibration z-score amplitude in CSV → retrain → document actual value.
**Never override model output in inference code.**

Risk level mapping: < 0.33 → LOW | 0.33–0.66 → MEDIUM | > 0.66 → HIGH

### Model Artifacts
Both `.pkl` files committed. Runnable: `cd src/backend && python -m app.ml.train_model`

---

## I. Evidence Layer (Member 3)

### EvidenceObject (Pydantic, in `evidence_engine.py`)
```python
class AnomalyEvidence(BaseModel):
    sensor: str
    severity: str    # NONE / LOW / MEDIUM / HIGH
    score: float

class MaintenanceEvidence(BaseModel):
    hours_since_service: float
    inspection_status: str   # CURRENT / DUE_SOON / OVERDUE

class EvidenceObject(BaseModel):
    asset_id: str
    component: str
    failure_risk: float      # 0.0–1.0
    risk_level: str          # LOW / MEDIUM / HIGH
    anomaly: AnomalyEvidence
    maintenance: MaintenanceEvidence
    criticality: str         # LOW / MEDIUM / HIGH
    mission_impact: str      # NONE / LOW / MEDIUM / HIGH
```

### `assemble_evidence(asset_id, db, mission_id=None) → EvidenceObject`
1. Fetch latest `Prediction` for `asset_id` from DB
2. Get `failure_probability`, `risk_level`, `anomaly_*` fields from Prediction
3. Fetch `Component` matching `prediction.component_id` → get `criticality`, `service_interval_hours`
4. Fetch latest `MaintenanceRecord` for that component → compute `hours_since_service`
5. Derive `inspection_status`: OVERDUE if `hours_since_service > service_interval_hours`; DUE_SOON if within 20% of interval; CURRENT otherwise
6. If `mission_id`: fetch `Mission`, parse `required_components` JSON → if at-risk component in list: `mission_impact = mission.criticality` else `mission_impact = "NONE"`
7. If no `mission_id`: `mission_impact = "NONE"`

**Rule**: No file downstream of `evidence_engine.py` fetches raw sensor or ML data directly.

**Member 3 writes the pure-function version first** (takes typed arguments, no `db` parameter) then wraps with DB session in a second pass.

---

## J. Readiness Engine (Member 3)

### `config.py` (Member 1 owns this file)
```python
READINESS_WEIGHTS = {
    "failure_risk": 0.40,
    "anomaly_severity": 0.25,
    "component_criticality": 0.20,
    "mission_impact": 0.15
}
READINESS_THRESHOLDS = {"ready_max": 0.34, "conditionally_ready_max": 0.66}
HARD_RULE_FAILURE_RISK_THRESHOLD = 0.85

MAINTENANCE_WEIGHTS = {
    "failure_risk": 0.35,
    "criticality": 0.25,
    "mission_impact": 0.25,
    "urgency": 0.15
}
```

### `compute_readiness(evidence: EvidenceObject, mission=None) → ReadinessResult`

```
Step 1 — Hard Rules (first match wins, return immediately):
  IF evidence.maintenance.inspection_status == "OVERDUE"
     AND evidence.criticality == "HIGH"
     → NOT_READY: "Mandatory inspection overdue on HIGH criticality component"

  IF evidence.failure_risk > HARD_RULE_FAILURE_RISK_THRESHOLD
     AND evidence.criticality == "HIGH"
     → NOT_READY: "Critical component failure risk exceeds hard threshold"

  IF mission AND evidence.component in mission.required_components
     AND component.status != "FUNCTIONAL"
     → NOT_READY: "Mission-required component is non-functional"

Step 2 — Weighted score (only if no hard rule fired):
  severity_map  = {NONE: 0.0, LOW: 0.33, MEDIUM: 0.67, HIGH: 1.0}
  criticality_map = {LOW: 0.33, MEDIUM: 0.67, HIGH: 1.0}
  impact_map    = {NONE: 0.0, LOW: 0.33, MEDIUM: 0.67, HIGH: 1.0}

  score = 0.40 × failure_risk
        + 0.25 × severity_map[anomaly.severity]
        + 0.20 × criticality_map[criticality]
        + 0.15 × impact_map[mission_impact]

Step 3 — Apply threshold:
  threshold = mission.readiness_threshold if mission else READINESS_THRESHOLDS
  score ≤ ready_max (0.34)           → READY
  score ≤ conditionally_ready_max    → CONDITIONALLY_READY
  else                               → NOT_READY
```

Mission-aware readiness is the same function — `assemble_evidence()` with `mission_id` produces different `mission_impact`.

---

## K. Mission Dataset

| Mission ID | Name | Criticality | Required Components | Readiness Threshold |
|---|---|---|---|---|
| MSN-001 | Routine Training | LOW | `[]` | global (0.66) |
| MSN-002 | Border Patrol | MEDIUM | `["main_bearing","hydraulics"]` | 0.60 |
| MSN-003 | High-Criticality Reconnaissance | HIGH | `["engine","sensors","avionics","communications"]` | 0.40 |

> Stealth systems removed. MSN-003 focuses on engine, sensors, avionics, communications.

AS-1047 expected results:
- MSN-001: no required components → hard rule on inspection may not fire → **CONDITIONALLY READY**
- MSN-003: bearing is HIGH criticality, inspection OVERDUE → hard rule fires → **NOT READY**

---

## L. Maintenance Priority Engine (Member 3)

### `rank_all_assets(db) → List[MaintenanceRecommendation]`
1. For each asset: `assemble_evidence(asset_id, db)` (no mission context)
2. Compute `urgency`: days until next mission requiring the at-risk component, normalised to 0–1 (`urgency = max(0, 1 − days/30)`; default 0.5 if no mission found)
3. `priority_score = 0.35×failure_risk + 0.25×criticality_norm + 0.25×mission_impact_norm + 0.15×urgency`
4. `action`: human-readable string, e.g. `"Inspect and replace main_bearing on AS-1047"`
5. `factors`: dict with all contributing values — Bob cites these in explanations
6. Sort descending; persist to `MaintenanceRecommendations`; return list

---

## M. Frontend Implementation (Member 4)

### Mock Layer
```
USE_MOCK=true  (in .env.local)
```
`api.ts` checks `import.meta.env.VITE_USE_MOCK === 'true'`; if true, returns from `mockData.ts` instead of making HTTP calls. `mockData.ts` contains realistic AS-1047 fixture objects matching contract shapes exactly.

**Member 4 switches `USE_MOCK=false` at Milestone B**, when the real backend is ready.

### Non-negotiable constraints
- `readiness_status`, `readiness_score`, `reasons`, `evidence` sourced exclusively from API response — no React computation
- All API calls go through `services/api.ts` — no inline `axios.get` in component files

### TypeScript types (`types/index.ts`)
```typescript
interface EvidenceObject {
  asset_id: string; component: string; failure_risk: number; risk_level: string;
  anomaly: { sensor: string; severity: string; score: number };
  maintenance: { hours_since_service: number; inspection_status: string };
  criticality: string; mission_impact: string;
}
interface ReadinessResult {
  asset_id: string; mission_id: string | null; status: string;
  score: number; reasons: string[]; evidence: EvidenceObject; computed_at: string;
}
interface Asset { id: string; name: string; type: string; status: string; location: string; total_flight_hours: number }
interface Prediction { asset_id: string; component: string; failure_probability: number; risk_level: string; created_at: string }
interface AnomalyResult { asset_id: string; anomaly_score: number; anomaly_status: string; sensor: string; severity: string }
interface MaintenancePriority { rank: number; asset_id: string; component: string; action: string; priority_score: number; urgency: number; factors: Record<string, unknown> }
interface Mission { id: string; name: string; criticality: string; required_components: string[]; readiness_threshold: number }
interface CopilotResponse { response: string; evidence_used: string[]; tools_called: string[] }
```

### Page–API mapping
| Page | API Endpoints |
|---|---|
| `Dashboard.tsx` | `GET /api/fleet/readiness`, `GET /api/maintenance/priorities` |
| `Assets.tsx` | `GET /api/assets` |
| `AssetDetails.tsx` | `/api/assets/{id}`, `/sensors`, `/predictions`, `/anomalies`, `/readiness` |
| `Predictions.tsx` | `/api/assets/{id}/predictions`, `/api/assets/{id}/anomalies` |
| `MaintenancePlan.tsx` | `GET /api/maintenance/priorities` |
| `Missions.tsx` | `GET /api/missions`, `GET /api/missions/{id}/readiness` |
| `Copilot.tsx` | `POST /api/copilot/chat` |

### Tailwind status colours
- `READY` → `bg-green-600`
- `CONDITIONALLY_READY` → `bg-yellow-500`
- `NOT_READY` → `bg-red-600`
- Dark base: `bg-slate-900` — military/operations aesthetic

---

## N. IBM Bob MCP Implementation (Member 3)

### `.bob/mcp.json`
```json
{
  "mcpServers": {
    "assetsentinel": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "app.mcp.server"],
      "cwd": "src/backend",
      "env": {
        "DATABASE_URL": "sqlite:///./assetsentinel.db"
      }
    }
  }
}
```

### `mcp/server.py` — 11 read-only tools
Each tool calls the same service functions as the REST API — no duplicated logic.

| Tool | Returns |
|---|---|
| `get_asset_status(asset_id)` | `{id, name, status, readiness_status, readiness_score, top_risk}` |
| `get_asset_details(asset_id)` | `{asset, components, total_flight_hours}` |
| `get_sensor_trends(asset_id)` | `{readings, trend_direction, anomalous_sensors}` |
| `get_component_health(asset_id)` | `{components: [{name, criticality, status, hours_since_service, inspection_status}]}` |
| `get_failure_predictions(asset_id)` | `{failure_probability, risk_level, component, created_at}` |
| `get_anomalies(asset_id)` | `{anomaly_score, anomaly_status, sensor, severity, detected_at}` |
| `get_maintenance_history(asset_id)` | `{records, hours_since_last, overdue}` |
| `get_mission_readiness(asset_id, mission_id)` | `{status, score, reasons, evidence, mission_name, mission_criticality}` |
| `get_fleet_readiness()` | `{total, ready, conditionally_ready, not_ready, assets}` |
| `get_maintenance_priorities()` | `{priorities: [{rank, asset_id, action, priority_score, factors}]}` |
| `get_mission_details(mission_id)` | `{id, name, criticality, required_components, readiness_threshold, scheduled_date}` |

### Bob system prompt (in `watsonx_service.py`)
```
You are AssetSentinel Copilot, an explainability assistant for a mission readiness system.
You explain pre-computed readiness results, failure predictions, anomaly detections, and
maintenance recommendations. Use your tools to retrieve data before answering.

CRITICAL RULES:
- You NEVER independently calculate or decide readiness status.
- The Readiness Engine has made the determination. Your role is to explain it.
- Always cite specific evidence values: failure probability, sensor name, hours since service.
- When stating NOT READY, attribute it to the Readiness Engine, not your own assessment.
- Always retrieve live data via tools before answering asset-specific questions.
```

### Canonical verification interaction
```
User: "Why is AS-1047 not mission-ready and what should we fix first?"

Bob calls:
  get_asset_status("AS-1047")
  get_failure_predictions("AS-1047")
  get_anomalies("AS-1047")
  get_mission_readiness("AS-1047", "MSN-003")
  get_maintenance_priorities()

Expected explanation:
  "The Readiness Engine determined AS-1047 is NOT READY for MSN-003.
   Main bearing failure probability: [actual value]. Vibration anomaly: HIGH.
   Bearing inspection is OVERDUE ([actual hours] hours since last service, 420h).
   Hard rule triggered: overdue mandatory inspection on a HIGH criticality component.
   Priority action #1: Inspect and replace main bearing."
```

---

## O. Testing Strategy

### Member 3 — Unit Tests (pure functions, no DB)
| File | Key assertions |
|---|---|
| `test_evidence_engine.py` | AS-1047 evidence fields correct; `mission_impact` changes with/without mission_id |
| `test_readiness_engine.py` | Hard rule: overdue+HIGH → NOT_READY; hard rule: risk>0.85+HIGH → NOT_READY; weighted score formula; CONDITIONALLY_READY path |
| `test_maintenance_optimizer.py` | AS-1047 ranks #1; `priority_score` uses correct weights; `action` string non-empty |

### Member 1 — Integration Tests
| File | Key assertions |
|---|---|
| `test_api_assets.py` | `GET /api/assets` → 200, non-empty list; `GET /api/assets/AS-1047` → correct fields |
| `test_api_readiness.py` | AS-1047 + MSN-003 → NOT_READY; AS-1047 + MSN-001 → CONDITIONALLY_READY; reasons non-empty |

### Member 2 — ML Tests
| File | Key assertions |
|---|---|
| `test_ml_pipeline.py` | Models load without error; AS-1047 isolation forest returns ANOMALOUS; AS-1047 RF output > 0.70; feature vector length matches expected |

### Run commands
```bash
cd src/backend && pytest tests/ -v
cd src/backend && pytest tests/test_readiness_engine.py -v
cd src/backend && pytest tests/test_readiness_engine.py::test_hard_rule_overdue_inspection -v
```

---

## P. Demo Strategy

### Pre-demo checklist
1. `cd src/backend && python -m app.ml.train_model`
2. `cd src/backend && python -m app.scripts.seed_db`
3. `cd src/backend && uvicorn app.main:app --reload`
4. `cd src/frontend && npm run dev`
5. IBM Bob running locally, `.bob/mcp.json` registered
6. Verify: `GET http://localhost:8000/api/assets/AS-1047` returns prediction + readiness

### 9-step demo script
1. **Dashboard** — fleet overview; AS-1047 flagged NOT READY
2. **Assets page** — AS-1047 in NOT READY badge
3. **Asset Details** — vibration trend chart (Recharts LineChart) showing upward deviation; anomaly HIGH
4. **Readiness panel** — NOT READY for MSN-003, reasons listed
5. **Switch to MSN-001** — same asset, same sensor data → CONDITIONALLY READY; explain mission context
6. **Maintenance Plan** — AS-1047 bearing is rank #1; factors table visible
7. **Missions page** — MSN-003 fleet table; AS-1047 is only NOT READY asset
8. **Copilot page** — type "Why is AS-1047 not mission-ready and what should we fix first?"
9. **Bob's response** — cites Readiness Engine, exact evidence values, recommends bearing action

---

## Q. Known Technical Risks

| Risk | Severity | Mitigation |
|---|---|---|
| RF produces < 0.75 for AS-1047 | HIGH | Increase vibration z-score amplitude in CSV; retrain; document actual value — never hardcode |
| MCP SDK package name unknown | HIGH | Verify `mcp` PyPI package before Phase 10; test minimal 1-tool server first |
| `.bob/mcp.json` STDIO syntax | MEDIUM | Validate with Bob's own MCP documentation before writing all 11 tools |
| Two members editing `main.py` concurrently | LOW | Member 1 owns `main.py`; others submit router files and Member 1 registers them |
| `required_components` JSON string parsing | LOW | Parse exclusively in service layer; never in ORM model or route handler |
| Pydantic v2 API | LOW | Use `model_validate`, `model_config`; never `from_orm`, `class Config` |
| SQLite concurrency | LOW | `check_same_thread=False` in engine; acceptable for MVP |
| GitHub Action validation failure | MEDIUM | Run all 6 checklist items locally before final push to main |
| Frontend `USE_MOCK` not toggled off | LOW | Milestone B checklist item: confirm `USE_MOCK=false` before Milestone C integration test |

---

## R. Git Branch Strategy

### Branch structure
```
main                  ← production-ready, protected; only merged via PR
└── develop           ← integration branch; all feature branches merge here first
    ├── feature/backend-infrastructure   (Member 1)
    ├── feature/ml-pipeline              (Member 2)
    ├── feature/decision-engines         (Member 3)
    └── feature/frontend                 (Member 4)
```

### Branch ownership
| Branch | Owner | Merges into |
|---|---|---|
| `feature/backend-infrastructure` | Member 1 | `develop` |
| `feature/ml-pipeline` | Member 2 | `develop` |
| `feature/decision-engines` | Member 3 | `develop` |
| `feature/frontend` | Member 4 | `develop` |

### Merge rules
- Each member merges their feature branch into `develop` at each milestone
- No member merges directly to `main`
- `main` receives a single squash-merge from `develop` for the final submission
- PR required for `develop` → `main` (reviewer: Member 1 or team lead)

### Conflict avoidance
- Member 1 owns `main.py`, `database.py`, `config.py`, `db/models.py` — no other member edits these
- Member 2 owns all of `routers/ml.py` — does not touch `routers/assets.py`
- Member 3 owns all of `routers/copilot.py`, `routers/maintenance_plan.py` — does not touch `routers/assets.py`
- Member 4 owns all of `frontend/` — no backend files
- `config.py` changes (weight/threshold tuning) by Member 3 go through Member 1 as a PR to avoid merge conflicts

### Day-by-day sequence
```
Day 1: All four create feature branches and push initial skeletons
Day 2: Member 1+2 reach Milestone A; merge backend-infrastructure + ml-pipeline to develop
Day 3: Member 3 reaches Milestone B; merge decision-engines to develop
Day 4: Member 4 reaches Milestone C; merge frontend to develop; all smoke-test on develop
Day 5: Member 3 reaches Milestone D; MCP + Copilot merged; full end-to-end demo verified on develop
Final: develop → main (squash PR); submission.yaml + README finalised; screenshots + video added
```

---

## S. First Agent-Mode Task

**Phase 0** — Fill hackathon submission metadata and documentation.

1. `submission.yaml` — all required fields:
   - `title`: "AssetSentinel — Mission Readiness & Predictive Maintenance Copilot"
   - `problem_statement`, `solution_summary`, `key_features` ×5, full `tech_stack` arrays, `what_we_are_most_proud_of`, `known_limitations`
2. `README.md` — replace every `[...]` placeholder
3. `docs/problem-statement.md` — AssetSentinel-specific content
4. `docs/solution-overview.md` — AssetSentinel-specific content
5. `docs/setup-guide.md` — draft with expected commands (finalise at Phase 11)
6. Create `docs/api-contract.md` — publish the API contract from Section D so all members can reference it

No code, no build setup. Ensures GitHub Action validation passes once Phase 1 adds the first `.py` file.

---

*Plan version: 3.0 — Adds parallel team structure, API contract, mock frontend layer, milestones A–D,
per-member file ownership, split maintenance routes, ML router separation, watsonx/Bob ownership to Member 3,
MSN-003 stealth removal, develop-branch git workflow*
