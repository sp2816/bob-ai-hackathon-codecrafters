# AssetSentinel — Shared Data Contracts

**Team:** Codecrafters
**Purpose:** Shared naming conventions, data contracts, enums, and module interfaces for integration between Member 1, Member 2, Member 3, and Member 4.

This document is the single source of truth for cross-module variable names and data structures.

All members MUST follow these contracts when exchanging data between modules.

---

# 1. Module Ownership

| Module                           | Owner       | Folder                               |
| -------------------------------- | ----------- | ------------------------------------ |
| Backend + Database + Security    | Dhruv       | `src/backend/member1_backend/`       |
| ML + Failure Prediction          | Selin       | `src/backend/member2_ml/`            |
| Readiness + Maintenance          | Tisha       | `src/backend/member3_readiness/`     |
| Frontend + Copilot + Integration | Mukt        | `src/frontend/`                      |
| Shared contracts                 | All members | `src/backend/integration/contracts/` |

Do not implement another member's functionality inside your own folder.

---

# 2. Naming Convention

## Python

Use `snake_case`:

```python
asset_id
component_id
failure_probability
risk_category
anomaly_score
readiness_score
mission_impact
```

## TypeScript

Use `camelCase` for local variables where appropriate, but API response field names MUST remain exactly as defined by the backend contract.

Example:

```typescript
const assetId = asset.asset_id;
```

Do NOT rename backend API fields when defining shared API types.

---

# 3. Canonical IDs

Use these exact field names:

```text
asset_id
component_id
sensor_id
maintenance_id
mission_id
prediction_id
recommendation_id
```

IDs are strings.

Example:

```text
AS-1047
```

---

# 4. Asset Contract

Canonical asset fields:

```text
asset_id
asset_name
asset_type
unit
operational_hours
current_status
readiness_score
```

Example:

```json
{
  "asset_id": "AS-1047",
  "asset_name": "Asset 1047",
  "asset_type": "aircraft",
  "unit": "Unit-A",
  "operational_hours": 2450.0,
  "current_status": "NOT_READY",
  "readiness_score": 0.82
}
```

---

# 5. Component Contract

Canonical component fields:

```text
component_id
asset_id
component_type
criticality
installation_date
operating_hours
life_limit
```

Allowed `criticality` values:

```text
LOW
MEDIUM
HIGH
```

---

# 6. Sensor Data Contract

Canonical fields:

```text
sensor_id
asset_id
component_id
timestamp
sensor_type
value
```

Allowed sensor types may include:

```text
vibration
temperature
pressure
RPM
```

Additional sensor types must be agreed upon before being introduced.

---

# 7. Maintenance Record Contract

Canonical fields:

```text
maintenance_id
asset_id
component_id
maintenance_type
maintenance_date
technician_action
status
notes
```

Allowed maintenance status values:

```text
COMPLETED
OVERDUE
SCHEDULED
```

---

# 8. ML Prediction Contract

Member 2 → Evidence Layer / Backend

Random Forest output MUST use:

```text
prediction_id
asset_id
component_id
failure_probability
risk_category
timestamp
```

Isolation Forest output MUST provide:

```text
asset_id
component_id
anomaly_score
anomaly_status
anomaly_severity
sensor
timestamp
```

Allowed risk categories:

```text
LOW
MEDIUM
HIGH
```

Allowed anomaly status:

```text
NORMAL
HIGH
```

Allowed anomaly severity:

```text
LOW
MEDIUM
HIGH
```

### Important distinction

`failure_probability` is NOT RUL.

The system must never convert it into:

```text
days_until_failure
hours_until_failure
remaining_useful_life
```

unless a separate validated RUL capability is implemented.

---

# 9. Evidence Layer Contract

The Evidence Layer is the shared decision-input representation.

Conceptual structure:

```json
{
  "asset_id": "AS-1047",
  "component": "bearing",
  "failure_risk": 0.87,
  "risk_level": "HIGH",
  "anomaly": {
    "sensor": "vibration",
    "severity": "HIGH"
  },
  "maintenance": {
    "hours_since_service": 420,
    "inspection_status": "OVERDUE"
  },
  "criticality": "HIGH",
  "mission_impact": "HIGH"
}
```

The Evidence Layer is the ONLY decision-input source for:

```text
Readiness Engine
Maintenance Priority Engine
IBM Bob
```

These components must NOT independently derive decision inputs from raw sensor rows or raw ML output.

---

# 10. Evidence Field Names

Use these exact names:

```text
asset_id
component
failure_risk
risk_level
anomaly
anomaly.sensor
anomaly.severity
maintenance
maintenance.hours_since_service
maintenance.inspection_status
criticality
mission_impact
```

---

# 11. Mission Contract

Canonical mission fields:

```text
mission_id
mission_name
mission_type
criticality
scheduled_time
required_components
readiness_threshold
```

Allowed mission criticality:

```text
LOW
MEDIUM
HIGH
```

Planned demo missions:

```text
MSN-001 → Training → LOW
MSN-002 → Patrol → MEDIUM
MSN-003 → Strike → HIGH
```

---

# 12. Mission Impact

Mission impact must be represented on a normalized 0–1 scale internally.

The mission-specific impact is derived from:

```text
mission.required_components
mission.criticality
```

Do not independently invent mission-impact calculations in different modules.

---

# 13. Readiness Result Contract

Canonical fields:

```text
asset_id
mission_id
readiness_score
readiness_status
reasons
evidence
timestamp
```

`mission_id` may be null for generic readiness.

Allowed readiness statuses:

```text
READY
CONDITIONALLY_READY
NOT_READY
```

`reasons` must be a list of human-readable strings.

Example:

```json
{
  "asset_id": "AS-1047",
  "mission_id": "MSN-003",
  "readiness_score": 0.82,
  "readiness_status": "NOT_READY",
  "reasons": [
    "Bearing inspection is overdue",
    "Critical component failure risk exceeds the configured threshold"
  ]
}
```

---

# 14. Readiness Engine Rules

Hard rules MUST execute before weighted scoring.

### Rule 1

Overdue mandatory inspection on a critical component:

```text
→ NOT_READY
```

### Rule 2

Critical component failure risk above the configured hard threshold:

```text
→ NOT_READY
```

### Rule 3

Mission-required component unavailable/non-functional:

```text
→ NOT_READY
```

These rules cannot be overridden by:

```text
Frontend
IBM Bob
ML model
Copilot
```

---

# 15. Readiness Score

When no hard rule fires:

```text
Readiness Risk Score =
    0.40 × Failure Risk
  + 0.25 × Anomaly Severity
  + 0.20 × Component Criticality
  + 0.15 × Mission Impact
```

All inputs must be normalized to:

```text
0.0 – 1.0
```

Initial status thresholds:

```text
0.00 – 0.34 → READY
0.35 – 0.66 → CONDITIONALLY_READY
0.67 – 1.00 → NOT_READY
```

Weights and thresholds MUST exist in one configuration location.

Do not duplicate these values throughout the codebase.

---

# 16. Maintenance Priority Contract

Canonical output fields:

```text
recommendation_id
asset_id
component_id
priority
action
reason
risk
mission_impact
urgency
status
```

Priority calculation:

```text
Maintenance Priority =
    w1 × Failure Risk
  + w2 × Component Criticality
  + w3 × Mission Impact
  + w4 × Urgency
```

Weights MUST be configurable.

Do not simply sort by failure probability.

---

# 17. Maintenance Recommendation Example

```json
{
  "recommendation_id": "REC-001",
  "asset_id": "AS-1047",
  "component_id": "BRG-1047",
  "priority": 1,
  "action": "Inspect bearing",
  "reason": "High failure risk, high criticality, and high mission impact",
  "risk": "HIGH",
  "mission_impact": "HIGH",
  "urgency": "HIGH",
  "status": "OPEN"
}
```

Do NOT hardcode AS-1047 as priority 1.

The ranking must emerge from the actual priority calculation.

---

# 18. Common Enum Values

Use uppercase values consistently.

### Criticality

```text
LOW
MEDIUM
HIGH
```

### Risk

```text
LOW
MEDIUM
HIGH
```

### Readiness

```text
READY
CONDITIONALLY_READY
NOT_READY
```

### Maintenance Status

```text
COMPLETED
OVERDUE
SCHEDULED
```

### Recommendation Status

```text
OPEN
IN_PROGRESS
RESOLVED
```

---

# 19. Module Dependency Direction

The intended data flow is:

```text
Member 1 — Backend/Data
        ↓
Member 2 — ML outputs
        ↓
Evidence Layer
        ↓
Readiness Engine
        ↓
Maintenance Priority Engine
        ↓
API
        ↓
Member 4 — Frontend/Copilot
```

Do not create circular dependencies.

---

# 20. Decision Boundary

### Member 2 owns:

```text
failure_probability
risk_category
anomaly_score
anomaly_status
anomaly_severity
```

### Member 3 owns:

```text
failure_risk
mission_impact
readiness_score
readiness_status
reasons
maintenance priority
recommendations
```

The Evidence Layer translates/combines upstream evidence into the structured form required by Member 3's decision engines.

---

# 21. Frontend Rule

Member 4 MUST NOT implement readiness logic.

The frontend only consumes:

```text
readiness_status
readiness_score
reasons
```

It must NOT contain:

```text
if failureRisk > threshold
```

or equivalent readiness calculations.

The backend Readiness Engine is the single authority.

---

# 22. IBM Bob Rule

IBM Bob receives structured results from the backend.

Bob may:

```text
Explain
Summarize
Recommend based on existing recommendations
```

Bob may NOT:

```text
Calculate readiness
Override readiness
Change readiness_status
Invent failure probabilities
Invent maintenance priorities
```

---

# 23. Canonical Demo Asset

The canonical asset is:

```text
AS-1047
```

Expected demo story:

```text
High vibration anomaly
        ↓
Isolation Forest → HIGH anomaly
        ↓
Random Forest → high failure probability
        ↓
Evidence Layer
        ↓
Readiness Engine
        ↓
High-criticality mission → NOT_READY
Training mission → CONDITIONALLY_READY
        ↓
Maintenance Priority
        ↓
Bearing inspection/replacement ranked highly
        ↓
IBM Bob explains the evidence chain
```

The actual model output must never be hardcoded.

---

# 24. Integration Rules

1. Do not rename shared fields without team agreement.
2. Do not silently change enum values.
3. Do not change API response shapes without notifying affected members.
4. Do not duplicate readiness calculations.
5. Do not duplicate maintenance-priority calculations.
6. Do not bypass the Evidence Layer for decision logic.
7. Do not modify another member's implementation folder.
8. If an interface must change, update this contract first and notify the affected member.
9. Prefer backward-compatible additions over renaming existing fields.
10. Never commit credentials or `.env` files.

---

# 25. Git Ownership Rule

Normal implementation changes must remain inside the member's assigned folder.

```text
Dhruv  → src/backend/member1_backend/
Selin  → src/backend/member2_ml/
Tisha  → src/backend/member3_readiness/
Mukt   → src/frontend/
```

The integration contract is shared.

Changes to:

```text
src/backend/integration/contracts/
```

must be coordinated with all affected members.

---

# 26. Source of Truth

This document defines integration naming and data contracts.

If implementation code and this document disagree:

1. Stop integration work.
2. Notify the affected members.
3. Agree on the correct contract.
4. Update this document.
5. Then update implementation code.

Do not independently create competing field names or data structures.
