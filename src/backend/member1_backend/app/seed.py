"""
Seed the database with canonical demo data.

Demo story (AS-1047):
  1. High vibration anomaly on bearing (BRG-1047)
  2. Bearing maintenance is OVERDUE (420h since last service)
  3. ML output (stored in predictions table): ~87% failure probability, HIGH risk
  4. MSN-003 (Strike — HIGH criticality) → NOT_READY  (hard rule fires)
  5. MSN-001 (Training — LOW criticality)  → CONDITIONALLY_READY

Run:
    cd src/backend/member1_backend
    python -m app.seed
"""

import json
from app.database import SessionLocal, engine, Base

# Register all models so Base.metadata knows about them
from app.models import (  # noqa: F401
    asset, component, sensor_data, maintenance_record,
    mission, prediction, anomaly, readiness_result, maintenance_recommendation,
)

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# ── Assets ────────────────────────────────────────────────────────────────────
ASSETS = [
    {
        "asset_id": "AS-1047",
        "asset_name": "Aircraft 1047",
        "asset_type": "aircraft",
        "unit": "Unit-A",
        "operational_hours": 2450.0,
        "current_status": "NOT_READY",
        "readiness_score": 0.82,
    },
    {
        "asset_id": "AS-1002",
        "asset_name": "Aircraft 1002",
        "asset_type": "aircraft",
        "unit": "Unit-B",
        "operational_hours": 1200.0,
        "current_status": "READY",
        "readiness_score": 0.18,
    },
    {
        "asset_id": "AS-1078",
        "asset_name": "Aircraft 1078",
        "asset_type": "aircraft",
        "unit": "Unit-A",
        "operational_hours": 3100.0,
        "current_status": "CONDITIONALLY_READY",
        "readiness_score": 0.51,
    },
]

# ── Components ─────────────────────────────────────────────────────────────────
COMPONENTS = [
    # AS-1047
    {"component_id": "BRG-1047", "asset_id": "AS-1047", "component_type": "bearing",       "criticality": "HIGH",   "installation_date": "2022-06-15", "operating_hours": 2450.0, "life_limit": 3000.0},
    {"component_id": "ENG-1047", "asset_id": "AS-1047", "component_type": "engine",        "criticality": "HIGH",   "installation_date": "2021-01-10", "operating_hours": 2450.0, "life_limit": 5000.0},
    # AS-1002
    {"component_id": "BRG-1002", "asset_id": "AS-1002", "component_type": "bearing",       "criticality": "HIGH",   "installation_date": "2023-01-20", "operating_hours": 1200.0, "life_limit": 3000.0},
    {"component_id": "ENG-1002", "asset_id": "AS-1002", "component_type": "engine",        "criticality": "HIGH",   "installation_date": "2023-01-20", "operating_hours": 1200.0, "life_limit": 5000.0},
]

# ── Sensor Data ────────────────────────────────────────────────────────────────
SENSOR_DATA = [
    # AS-1047 bearing — elevated vibration (anomalous)
    {"sensor_id": "SEN-D-001", "asset_id": "AS-1047", "component_id": "BRG-1047", "timestamp": "2024-05-01T08:00:00", "sensor_type": "vibration",   "value": 9.8},
    {"sensor_id": "SEN-D-002", "asset_id": "AS-1047", "component_id": "BRG-1047", "timestamp": "2024-05-01T09:00:00", "sensor_type": "vibration",   "value": 10.3},
    {"sensor_id": "SEN-D-003", "asset_id": "AS-1047", "component_id": "BRG-1047", "timestamp": "2024-05-01T10:00:00", "sensor_type": "vibration",   "value": 11.1},
    {"sensor_id": "SEN-D-004", "asset_id": "AS-1047", "component_id": "BRG-1047", "timestamp": "2024-05-01T11:00:00", "sensor_type": "vibration",   "value": 10.7},
    {"sensor_id": "SEN-D-005", "asset_id": "AS-1047", "component_id": "ENG-1047", "timestamp": "2024-05-01T08:00:00", "sensor_type": "temperature",  "value": 88.5},
    {"sensor_id": "SEN-D-006", "asset_id": "AS-1047", "component_id": "ENG-1047", "timestamp": "2024-05-01T09:00:00", "sensor_type": "RPM",          "value": 3200.0},
    # AS-1002 — normal readings
    {"sensor_id": "SEN-D-007", "asset_id": "AS-1002", "component_id": "BRG-1002", "timestamp": "2024-05-01T08:00:00", "sensor_type": "vibration",   "value": 2.1},
    {"sensor_id": "SEN-D-008", "asset_id": "AS-1002", "component_id": "BRG-1002", "timestamp": "2024-05-01T09:00:00", "sensor_type": "vibration",   "value": 1.9},
]

# ── Maintenance Records ────────────────────────────────────────────────────────
MAINTENANCE_RECORDS = [
    {
        "maintenance_id": "MNT-1047-001",
        "asset_id": "AS-1047",
        "component_id": "BRG-1047",
        "maintenance_type": "inspection",
        "maintenance_date": "2024-02-10",
        "technician_action": "Routine bearing inspection — passed",
        "status": "OVERDUE",
        "hours_since_service": 420.0,
        "notes": "Last service 420h ago. Next inspection overdue.",
    },
    {
        "maintenance_id": "MNT-1047-002",
        "asset_id": "AS-1047",
        "component_id": "ENG-1047",
        "maintenance_type": "service",
        "maintenance_date": "2024-04-20",
        "technician_action": "Engine oil change and filter replacement",
        "status": "COMPLETED",
        "hours_since_service": 250.0,
        "notes": None,
    },
    {
        "maintenance_id": "MNT-1002-001",
        "asset_id": "AS-1002",
        "component_id": "BRG-1002",
        "maintenance_type": "inspection",
        "maintenance_date": "2024-04-28",
        "technician_action": "Bearing inspection — passed, no issues found",
        "status": "COMPLETED",
        "hours_since_service": 120.0,
        "notes": None,
    },
    {
        "maintenance_id": "MNT-1002-002",
        "asset_id": "AS-1002",
        "component_id": "ENG-1002",
        "maintenance_type": "service",
        "maintenance_date": "2024-04-25",
        "technician_action": "Engine routine maintenance",
        "status": "COMPLETED",
        "hours_since_service": 100.0,
        "notes": None,
    },
]

# ── Missions ──────────────────────────────────────────────────────────────────
MISSIONS = [
    {
        "mission_id": "MSN-001",
        "mission_name": "Training Exercise Alpha",
        "mission_type": "Training",
        "criticality": "LOW",
        "scheduled_time": "2024-05-10T06:00:00",
        "required_components": json.dumps(["engine", "sensors"]),
        "readiness_threshold": 0.66,
    },
    {
        "mission_id": "MSN-002",
        "mission_name": "Coastal Patrol Bravo",
        "mission_type": "Patrol",
        "criticality": "MEDIUM",
        "scheduled_time": "2024-05-12T08:00:00",
        "required_components": json.dumps(["engine", "sensors", "avionics"]),
        "readiness_threshold": 0.66,
    },
    {
        "mission_id": "MSN-003",
        "mission_name": "Strike Mission Delta",
        "mission_type": "Strike",
        "criticality": "HIGH",
        "scheduled_time": "2024-05-15T04:00:00",
        "required_components": json.dumps(["engine", "sensors", "avionics", "communications"]),
        "readiness_threshold": 0.34,
    },
]

# ── Predictions (normally written by Member 2 — seeded here for demo) ─────────
# NOTE: failure_probability comes from real model inference in production.
# This seed value approximates what the Random Forest outputs for AS-1047.
PREDICTIONS = [
    {
        "prediction_id": "PRED-1047-001",
        "asset_id": "AS-1047",
        "component_id": "BRG-1047",
        "failure_probability": 0.87,
        "risk_category": "HIGH",
        "timestamp": "2024-05-01T11:30:00",
    },
    {
        "prediction_id": "PRED-1002-001",
        "asset_id": "AS-1002",
        "component_id": "BRG-1002",
        "failure_probability": 0.12,
        "risk_category": "LOW",
        "timestamp": "2024-05-01T11:30:00",
    },
]

# ── Anomalies (normally written by Member 2 — seeded here for demo) ───────────
# Contract §8 — Isolation Forest output fields:
#   asset_id, component_id, anomaly_score, anomaly_status,
#   anomaly_severity, sensor, timestamp
# anomaly_status  : NORMAL | HIGH
# anomaly_severity: LOW | MEDIUM | HIGH
ANOMALIES = [
    {
        "anomaly_id": "ANO-1047-001",
        "asset_id": "AS-1047",
        "component_id": "BRG-1047",
        "anomaly_score": -0.42,
        "anomaly_status": "HIGH",
        "anomaly_severity": "HIGH",
        "sensor": "vibration",
        "timestamp": "2024-05-01T11:00:00",
    },
    {
        "anomaly_id": "ANO-1002-001",
        "asset_id": "AS-1002",
        "component_id": "BRG-1002",
        "anomaly_score": 0.15,
        "anomaly_status": "NORMAL",
        "anomaly_severity": "LOW",
        "sensor": "vibration",
        "timestamp": "2024-05-01T11:00:00",
    },
]

# ── Readiness Results (normally written by Member 3 — seeded for demo) ────────
READINESS_RESULTS = [
    {
        "result_id": "RDY-1047-MSN003",
        "asset_id": "AS-1047",
        "mission_id": "MSN-003",
        "readiness_score": 0.82,
        "readiness_status": "NOT_READY",
        "reasons": json.dumps([
            "Bearing inspection is overdue on a critical component",
            "Critical component failure risk exceeds the configured threshold",
        ]),
        "evidence": json.dumps({
            "asset_id": "AS-1047",
            "component": "bearing",
            "failure_risk": 0.87,
            "risk_level": "HIGH",
            "anomaly": {"sensor": "vibration", "severity": "HIGH"},
            "maintenance": {"hours_since_service": 420, "inspection_status": "OVERDUE"},
            "criticality": "HIGH",
            "mission_impact": "HIGH",
        }),
        "timestamp": "2024-05-01T12:00:00",
    },
    {
        "result_id": "RDY-1047-MSN001",
        "asset_id": "AS-1047",
        "mission_id": "MSN-001",
        "readiness_score": 0.52,
        "readiness_status": "CONDITIONALLY_READY",
        "reasons": json.dumps([
            "High bearing failure risk detected",
            "Bearing inspection overdue but mission criticality is LOW",
        ]),
        "evidence": json.dumps({
            "asset_id": "AS-1047",
            "component": "bearing",
            "failure_risk": 0.87,
            "risk_level": "HIGH",
            "anomaly": {"sensor": "vibration", "severity": "HIGH"},
            "maintenance": {"hours_since_service": 420, "inspection_status": "OVERDUE"},
            "criticality": "HIGH",
            "mission_impact": "LOW",
        }),
        "timestamp": "2024-05-01T12:00:00",
    },
]

# ── Maintenance Recommendations (normally written by Member 3 — seeded for demo)
RECOMMENDATIONS = [
    {
        "recommendation_id": "REC-001",
        "asset_id": "AS-1047",
        "component_id": "BRG-1047",
        "priority": 1,
        "action": "Inspect and replace bearing",
        "reason": "High failure risk (87%), HIGH criticality, overdue inspection, HIGH mission impact",
        "risk": "HIGH",
        "mission_impact": "HIGH",
        "urgency": "HIGH",
        "status": "OPEN",
    },
    {
        "recommendation_id": "REC-002",
        "asset_id": "AS-1078",
        "component_id": "ENG-1078",
        "priority": 2,
        "action": "Schedule engine service",
        "reason": "Operating hours approaching service interval",
        "risk": "MEDIUM",
        "mission_impact": "MEDIUM",
        "urgency": "MEDIUM",
        "status": "OPEN",
    },
]


def seed():
    from app.models.asset import Asset
    from app.models.component import Component
    from app.models.sensor_data import SensorData
    from app.models.maintenance_record import MaintenanceRecord
    from app.models.mission import Mission
    from app.models.prediction import Prediction
    from app.models.anomaly import Anomaly
    from app.models.readiness_result import ReadinessResult
    from app.models.maintenance_recommendation import MaintenanceRecommendation

    counts = {k: 0 for k in ["assets", "components", "sensor_data", "maintenance",
                               "missions", "predictions", "anomalies", "readiness", "recommendations"]}

    for row in ASSETS:
        if not db.get(Asset, row["asset_id"]):
            db.add(Asset(**row)); counts["assets"] += 1

    for row in COMPONENTS:
        if not db.get(Component, row["component_id"]):
            db.add(Component(**row)); counts["components"] += 1

    for row in SENSOR_DATA:
        if not db.get(SensorData, row["sensor_id"]):
            db.add(SensorData(**row)); counts["sensor_data"] += 1

    for row in MAINTENANCE_RECORDS:
        if not db.get(MaintenanceRecord, row["maintenance_id"]):
            db.add(MaintenanceRecord(**row)); counts["maintenance"] += 1

    for row in MISSIONS:
        if not db.get(Mission, row["mission_id"]):
            db.add(Mission(**row)); counts["missions"] += 1

    for row in PREDICTIONS:
        if not db.get(Prediction, row["prediction_id"]):
            db.add(Prediction(**row)); counts["predictions"] += 1

    for row in ANOMALIES:
        if not db.get(Anomaly, row["anomaly_id"]):
            db.add(Anomaly(**row)); counts["anomalies"] += 1

    for row in READINESS_RESULTS:
        if not db.get(ReadinessResult, row["result_id"]):
            db.add(ReadinessResult(**row)); counts["readiness"] += 1

    for row in RECOMMENDATIONS:
        if not db.get(MaintenanceRecommendation, row["recommendation_id"]):
            db.add(MaintenanceRecommendation(**row)); counts["recommendations"] += 1

    db.commit()
    print("Seed complete:")
    for k, v in counts.items():
        print(f"    {k}: {v} inserted")


if __name__ == "__main__":
    seed()
