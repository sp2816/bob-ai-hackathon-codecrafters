"""
AssetSentinel — Asset Intake Service
src/backend/member1_backend/app/services/asset_intake_service.py

Purpose:
    Orchestrates the full Add Asset & Analyze pipeline:
        1. Validate asset/component ID uniqueness
        2. Run single-component ML inference (in memory, no CSV read, no fleet rerun)
        3. Run single-asset readiness + maintenance priority
        4. Persist all results to SQLite in one transaction
        5. Append to CSVs (ML compatibility layer, best-effort)

Architecture notes:
    - SQLite (~/.assetsentinel/assetsentinel.db) = application system of record
    - CSVs (member2_ml/data/*.csv) = ML compatibility layer for future fleet reruns
    - All readiness/risk/maintenance values come from Member 2 and Member 3 services
    - No business logic is implemented here — this is pure orchestration
"""

from __future__ import annotations

import csv
import json
import logging
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

# ---------------------------------------------------------------------------
# Sys path setup — allows importing member2_ml and member3_readiness
# ---------------------------------------------------------------------------
_BACKEND_ROOT = Path(__file__).resolve().parents[3]   # …/src/backend/
_MEMBER2_PATH = _BACKEND_ROOT / "member2_ml"
_MEMBER3_PATH = _BACKEND_ROOT / "member3_readiness"
_MEMBER3_PARENT = _MEMBER3_PATH.parent

for _p in [str(_MEMBER2_PATH), str(_BACKEND_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ---------------------------------------------------------------------------
# Imports from other members
# ---------------------------------------------------------------------------
from services.single_component_inference import predict_single_component_asset  # member2
from member3_readiness.evidence.models import ComponentInfo, MaintenanceInfo     # member3
from member3_readiness.services.readiness_service import ReadinessService        # member3

# ---------------------------------------------------------------------------
# Member 1 DB models
# ---------------------------------------------------------------------------
from app.models.asset import Asset
from app.models.anomaly import Anomaly
from app.models.component import Component
from app.models.maintenance_record import MaintenanceRecord
from app.models.maintenance_recommendation import MaintenanceRecommendation
from app.models.prediction import Prediction
from app.models.readiness_result import ReadinessResult
from app.schemas.asset_create import AssetCreateRequest, AssetCreateResponse

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CSV paths (ML compatibility layer)
# ---------------------------------------------------------------------------
_CSV_DIR         = _MEMBER2_PATH / "data"
_ASSETS_CSV      = _CSV_DIR / "assets.csv"
_COMPONENTS_CSV  = _CSV_DIR / "components.csv"
_SENSORS_CSV     = _CSV_DIR / "sensor_data.csv"
_MAINTENANCE_CSV = _CSV_DIR / "maintenance_records.csv"


# ===========================================================================
# Public entry point
# ===========================================================================

def create_asset_and_analyze(db: Session, request: AssetCreateRequest) -> dict:
    """
    Full Add Asset & Analyze pipeline.

    Returns a dict matching AssetCreateResponse schema.
    Raises HTTPException-compatible exceptions on validation failures.
    """
    # ── Step 1: Validate uniqueness ───────────────────────────────────────
    _validate_uniqueness(db, request.asset_id, request.component.component_id)

    # ── Step 2: Derived fields ────────────────────────────────────────────
    hours_at_last_service = max(
        0.0,
        request.component.operating_hours - request.maintenance.hours_since_service,
    )

    # ── Step 3: Single-component ML inference (in memory, no fleet rerun) ─
    logger.info("[intake] Running single-component ML inference for %s/%s",
                request.asset_id, request.component.component_id)

    sensor_values = {
        "vibration":   request.sensors.vibration,
        "temperature": request.sensors.temperature,
        "pressure":    request.sensors.pressure,
        "RPM":         request.sensors.RPM,
    }

    ml_result = predict_single_component_asset(
        asset_id=request.asset_id,
        component_id=request.component.component_id,
        component_type=request.component.component_type,
        criticality=request.component.criticality,
        operating_hours=request.component.operating_hours,
        life_limit=request.component.life_limit,
        service_interval_hours=request.component.service_interval_hours,
        hours_since_service=request.maintenance.hours_since_service,
        sensor_values=sensor_values,
        condition=request.sensors.condition,
    )

    logger.info("[intake] ML result: prob=%.3f risk=%s anomaly=%s",
                ml_result.failure_probability, ml_result.risk_category, ml_result.anomaly_status)

    # ── Step 4: Single-asset readiness + maintenance priority ─────────────
    readiness_result, mission_results, maintenance_recs = _run_single_asset_readiness(db, request, ml_result)

    logger.info("[intake] Readiness: %s (score=%.3f)",
                readiness_result.readiness_status, readiness_result.readiness_score)

    # ── Step 5: Persist everything to SQLite in one transaction ───────────
    asset_row, pred_row, anom_row, rec_row = _persist_all(
        db, request, ml_result, readiness_result, mission_results, maintenance_recs,
        hours_at_last_service,
    )

    # ── Step 6: Append to CSVs (ML compatibility layer, best-effort) ──────
    try:
        _append_to_csvs(request, sensor_values, hours_at_last_service)
        logger.info("[intake] CSV append complete (ML compatibility layer)")
    except Exception as csv_err:
        # CSV append is best-effort — SQLite is the source of truth
        logger.warning("[intake] CSV append failed (non-fatal): %s", csv_err)

    # ── Step 7: Build response ────────────────────────────────────────────
    return _build_response(asset_row, pred_row, anom_row, readiness_result, rec_row)


# ===========================================================================
# Validation
# ===========================================================================

def _validate_uniqueness(db: Session, asset_id: str, component_id: str) -> None:
    if db.query(Asset).filter(Asset.asset_id == asset_id).first():
        raise ValueError(f"Asset ID '{asset_id}' already exists in the database.")
    if db.query(Component).filter(Component.component_id == component_id).first():
        raise ValueError(f"Component ID '{component_id}' already exists in the database.")


# ===========================================================================
# Single-asset readiness pipeline
# ===========================================================================

def _run_single_asset_readiness(db: Session, request: AssetCreateRequest, ml_result):
    """
    Run Member 3's Readiness Engine for this single new asset only.
    Does NOT re-run the entire fleet.
    """
    from member2_ml.services.prediction_service import ComponentPredictionResult as CPR
    from member3_readiness.missions.models import MissionInfo
    from app.models.mission import Mission
    import json

    cpr = CPR(
        prediction_id=ml_result.prediction_id,
        asset_id=ml_result.asset_id,
        component_id=ml_result.component_id,
        failure_probability=ml_result.failure_probability,
        risk_category=ml_result.risk_category,
        anomaly_score=ml_result.anomaly_score,
        anomaly_status=ml_result.anomaly_status,
        anomaly_severity=ml_result.anomaly_severity,
        sensor=ml_result.sensor,
        timestamp=ml_result.timestamp,
    )

    c_info = ComponentInfo(
        component_id=request.component.component_id,
        asset_id=request.asset_id,
        component_type=request.component.component_type,
        criticality=request.component.criticality,
    )

    maint_date = datetime.strptime(request.maintenance.maintenance_date, "%Y-%m-%d")
    m_info = MaintenanceInfo(
        maintenance_id=f"MNT-NEW-{request.component.component_id}",
        asset_id=request.asset_id,
        component_id=request.component.component_id,
        maintenance_type=request.maintenance.maintenance_type,
        maintenance_date=maint_date,
        status=request.maintenance.status,
        hours_since_service=request.maintenance.hours_since_service,
        technician_action=request.maintenance.technician_action,
        notes=request.maintenance.notes,
    )

    evidence = ReadinessService.build_component_evidence(cpr, c_info, m_info)
    readiness = ReadinessService.evaluate_asset_readiness([evidence])

    # Mission readiness
    missions = db.query(Mission).all()
    mission_infos = []
    for m in missions:
        req_comps = json.loads(m.required_components) if m.required_components else []
        try:
            m_time = datetime.fromisoformat(m.scheduled_time)
        except ValueError:
            m_time = datetime.strptime(m.scheduled_time, "%Y-%m-%dT%H:%M:%S")

        m_info = MissionInfo(
            mission_id=m.mission_id,
            mission_name=m.mission_name,
            mission_type=m.mission_type,
            criticality=m.criticality,
            scheduled_time=m_time,
            required_components=req_comps,
            readiness_threshold=m.readiness_threshold
        )
        mission_infos.append(m_info)
        
    mission_results = []
    for m_info in mission_infos:
        m_res = ReadinessService.evaluate_mission_readiness([evidence], m_info)
        mission_results.append(m_res)

    # Build component_id_map for maintenance ranking
    component_id_map = {
        (request.asset_id, request.component.component_type): request.component.component_id
    }
    recommendations = ReadinessService.rank_maintenance_actions([evidence], component_id_map)

    return readiness, mission_results, recommendations


# ===========================================================================
# SQLite persistence
# ===========================================================================

def _persist_all(
    db: Session,
    request: AssetCreateRequest,
    ml_result,
    readiness_result,
    mission_results,
    maintenance_recs,
    hours_at_last_service: float,
):
    """Persist all records to SQLite in a single transaction."""
    now_ts = datetime.now(timezone.utc).isoformat()

    # ── Asset ──────────────────────────────────────────────────────────────
    new_asset = Asset(
        asset_id=request.asset_id,
        asset_name=request.asset_name,
        asset_type=request.asset_type,
        unit=request.unit,
        operational_hours=request.operational_hours,
        current_status=readiness_result.readiness_status,
        readiness_score=readiness_result.readiness_score,
    )
    db.add(new_asset)

    # ── Component ──────────────────────────────────────────────────────────
    new_comp = Component(
        component_id=request.component.component_id,
        asset_id=request.asset_id,
        component_type=request.component.component_type,
        criticality=request.component.criticality,
        installation_date=request.component.installation_date,
        operating_hours=request.component.operating_hours,
        life_limit=request.component.life_limit,
    )
    db.add(new_comp)

    # ── Maintenance record ─────────────────────────────────────────────────
    maint_id = f"MNT-{request.component.component_id}-001"
    new_maint = MaintenanceRecord(
        maintenance_id=maint_id,
        asset_id=request.asset_id,
        component_id=request.component.component_id,
        maintenance_type=request.maintenance.maintenance_type,
        maintenance_date=request.maintenance.maintenance_date,
        technician_action=request.maintenance.technician_action,
        status=request.maintenance.status,
        hours_since_service=request.maintenance.hours_since_service,
        notes=request.maintenance.notes or "",
    )
    db.add(new_maint)

    # ── Prediction ─────────────────────────────────────────────────────────
    pred_row = Prediction(
        prediction_id=ml_result.prediction_id,
        asset_id=ml_result.asset_id,
        component_id=ml_result.component_id,
        failure_probability=ml_result.failure_probability,
        risk_category=ml_result.risk_category,
        timestamp=ml_result.timestamp,
    )
    db.add(pred_row)

    # ── Anomaly ────────────────────────────────────────────────────────────
    anomaly_id = f"ANO-{request.asset_id}-{request.component.component_id}-{now_ts[:10]}"
    anom_row = Anomaly(
        anomaly_id=anomaly_id,
        asset_id=ml_result.asset_id,
        component_id=ml_result.component_id,
        anomaly_score=ml_result.anomaly_score,
        anomaly_status=ml_result.anomaly_status,
        anomaly_severity=ml_result.anomaly_severity,
        sensor=ml_result.sensor,
        timestamp=ml_result.timestamp,
    )
    db.add(anom_row)

    # ── Readiness result ───────────────────────────────────────────────────
    rid = f"RDY-{request.asset_id}-GENERIC"
    rdy_row = ReadinessResult(
        result_id=rid,
        asset_id=request.asset_id,
        mission_id=None,
        readiness_score=readiness_result.readiness_score,
        readiness_status=readiness_result.readiness_status,
        reasons=json.dumps(readiness_result.reasons),
        evidence=json.dumps([e.model_dump() for e in readiness_result.evidence]),
        timestamp=readiness_result.timestamp,
    )
    db.add(rdy_row)
    
    # ── Mission Readiness results ─────────────────────────────────────────
    for m_res in mission_results:
        m_rid = f"RDY-{request.asset_id}-{m_res.mission_id}"
        m_row = ReadinessResult(
            result_id=m_rid,
            asset_id=request.asset_id,
            mission_id=m_res.mission_id,
            readiness_score=m_res.readiness_score,
            readiness_status=m_res.readiness_status,
            reasons=json.dumps(m_res.reasons),
            evidence=json.dumps([e.model_dump() for e in m_res.evidence]),
            timestamp=m_res.timestamp,
        )
        db.add(m_row)

    # ── Maintenance recommendations ────────────────────────────────────────
    rec_row = None
    for rec in maintenance_recs:
        new_rec = MaintenanceRecommendation(
            recommendation_id=rec.recommendation_id,
            asset_id=rec.asset_id,
            component_id=rec.component_id,
            priority=rec.priority,
            action=rec.action,
            reason=rec.reason,
            risk=rec.risk,
            mission_impact=rec.mission_impact,
            urgency=rec.urgency,
            status=rec.status,
        )
        db.add(new_rec)
        if rec_row is None:
            rec_row = new_rec  # highest priority (first in ranked list)

    db.commit()
    db.refresh(new_asset)

    return new_asset, pred_row, anom_row, rec_row


# ===========================================================================
# CSV append (ML compatibility layer)
# ===========================================================================

def _append_to_csvs(
    request: AssetCreateRequest,
    sensor_values: dict[str, float],
    hours_at_last_service: float,
) -> None:
    """
    Append the new asset's data to the member2_ml CSV files so future
    fleet-wide ML runs (via /fleet/run-ml) include this asset.

    SQLite is the application system of record.
    CSVs are the current ML inference/training compatibility input.
    """
    # assets.csv
    _append_csv_row(_ASSETS_CSV, {
        "asset_id":          request.asset_id,
        "asset_name":        request.asset_name,
        "asset_type":        request.asset_type,
        "unit":              request.unit,
        "operational_hours": request.operational_hours,
        "current_status":    "UNKNOWN",
    })

    # components.csv (includes ML-specific fields not in SQLite Component model)
    _append_csv_row(_COMPONENTS_CSV, {
        "component_id":           request.component.component_id,
        "asset_id":               request.asset_id,
        "component_type":         request.component.component_type,
        "criticality":            request.component.criticality,
        "installation_date":      request.component.installation_date or "2024-01-01",
        "operating_hours":        request.component.operating_hours,
        "life_limit":             request.component.life_limit or request.component.operating_hours * 2,
        "service_interval_hours": request.component.service_interval_hours,
        "hours_at_last_service":  hours_at_last_service,
    })

    # sensor_data.csv — deterministic synthetic window
    from services.single_component_inference import build_deterministic_sensor_window
    sensor_df = build_deterministic_sensor_window(
        request.asset_id,
        request.component.component_id,
        sensor_values,
        request.sensors.condition,
    )
    with open(_SENSORS_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["sensor_id", "asset_id", "component_id", "timestamp", "sensor_type", "value"])
        for _, row in sensor_df.iterrows():
            writer.writerow({
                "sensor_id":    row["sensor_id"],
                "asset_id":     row["asset_id"],
                "component_id": row["component_id"],
                "timestamp":    row["timestamp"],
                "sensor_type":  row["sensor_type"],
                "value":        row["value"],
            })

    # maintenance_records.csv
    _append_csv_row(_MAINTENANCE_CSV, {
        "maintenance_id":   f"MNT-{request.component.component_id}-001",
        "asset_id":         request.asset_id,
        "component_id":     request.component.component_id,
        "maintenance_type": request.maintenance.maintenance_type,
        "maintenance_date": request.maintenance.maintenance_date,
        "technician_action": request.maintenance.technician_action,
        "status":           request.maintenance.status,
        "notes":            request.maintenance.notes or "",
    })


def _append_csv_row(csv_path: Path, row: dict) -> None:
    """Append a single row to a CSV, using existing headers."""
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        writer.writerow(row)


# ===========================================================================
# Response builder
# ===========================================================================

def _build_response(asset_row, pred_row, anom_row, readiness_result, rec_row) -> dict:
    """Build the AssetCreateResponse dict from persisted rows."""
    return {
        "asset": {
            "asset_id":          asset_row.asset_id,
            "asset_name":        asset_row.asset_name,
            "asset_type":        asset_row.asset_type,
            "unit":              asset_row.unit,
            "operational_hours": asset_row.operational_hours,
            "current_status":    asset_row.current_status,
            "readiness_score":   asset_row.readiness_score,
        },
        "prediction": {
            "prediction_id":       pred_row.prediction_id,
            "failure_probability": pred_row.failure_probability,
            "risk_category":       pred_row.risk_category,
        },
        "anomaly": {
            "anomaly_id":       anom_row.anomaly_id,
            "anomaly_status":   anom_row.anomaly_status,
            "anomaly_severity": anom_row.anomaly_severity,
            "sensor":           anom_row.sensor,
        },
        "readiness": {
            "readiness_status": readiness_result.readiness_status,
            "readiness_score":  readiness_result.readiness_score,
            "reasons":          readiness_result.reasons or [],
        },
        "recommendation": {
            "recommendation_id": rec_row.recommendation_id,
            "action":            rec_row.action,
            "priority":          rec_row.priority,
            "urgency":           rec_row.urgency,
            "risk":              rec_row.risk,
        } if rec_row else None,
        "pipeline_note": "Single-component inference completed. Fleet-wide pipeline not re-run.",
    }
