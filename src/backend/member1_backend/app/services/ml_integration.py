"""
ML Integration Bridge — Member 1 Backend
src/backend/member1_backend/app/services/ml_integration.py

Purpose:
    Calls Member 2's MLPredictionService, then saves the results
    into Member 1's predictions and anomalies tables.

Architecture position:
    Member 2 ML (prediction_service.py)
            ↓  returns ComponentPredictionResult list
    THIS FILE  (ml_integration.py)
            ↓  splits into Prediction + Anomaly rows
    Member 1 DB (predictions + anomalies tables)
            ↓
    Member 3 Evidence Layer reads from these tables

Usage:
    from app.services.ml_integration import run_ml_and_store
    run_ml_and_store(db)
"""

import sys
import os
from pathlib import Path
from sqlalchemy.orm import Session

# ── Add Member 2's folder to Python path so we can import her service ─────────
_MEMBER2_PATH = Path(__file__).resolve().parents[3] / "member2_ml"
if str(_MEMBER2_PATH) not in sys.path:
    sys.path.insert(0, str(_MEMBER2_PATH))

from app.models.prediction import Prediction
from app.models.anomaly import Anomaly


def run_ml_and_store(db: Session) -> dict:
    """
    Run Member 2's ML pipeline and persist results into Member 1's DB.

    Splits each ComponentPredictionResult into:
      - A Prediction row  (Random Forest fields)
      - An Anomaly row    (Isolation Forest fields) — only if anomaly_status == HIGH

    Returns a summary dict: {"predictions": int, "anomalies": int}
    """
    try:
        from services.prediction_service import predict_all_components
    except ImportError as e:
        raise RuntimeError(
            f"Cannot import Member 2 ML service. "
            f"Make sure member2_ml is on the Python path. Details: {e}"
        )

    results = predict_all_components()
    pred_count = 0
    anom_count = 0

    for r in results:
        # ── Save Random Forest output → predictions table ──────────────────
        existing_pred = (
            db.query(Prediction)
            .filter(
                Prediction.asset_id == r.asset_id,
                Prediction.component_id == r.component_id,
            )
            .first()
        )
        if existing_pred:
            # Update in place so Member 3 always sees latest
            existing_pred.prediction_id = r.prediction_id
            existing_pred.failure_probability = r.failure_probability
            existing_pred.risk_category = r.risk_category
            existing_pred.timestamp = r.timestamp
        else:
            db.add(Prediction(
                prediction_id=r.prediction_id,
                asset_id=r.asset_id,
                component_id=r.component_id,
                failure_probability=r.failure_probability,
                risk_category=r.risk_category,
                timestamp=r.timestamp,
            ))
        pred_count += 1

        # ── Save Isolation Forest output → anomalies table ─────────────────
        # Store all anomaly results (NORMAL and HIGH) so Member 3 has full picture
        anomaly_id = f"ANO-{r.asset_id}-{r.component_id}-{r.timestamp[:10]}"
        existing_anom = db.get(Anomaly, anomaly_id)
        if existing_anom:
            existing_anom.anomaly_score = r.anomaly_score
            existing_anom.anomaly_status = r.anomaly_status
            existing_anom.anomaly_severity = r.anomaly_severity
            existing_anom.sensor = r.sensor
            existing_anom.timestamp = r.timestamp
        else:
            db.add(Anomaly(
                anomaly_id=anomaly_id,
                asset_id=r.asset_id,
                component_id=r.component_id,
                anomaly_score=r.anomaly_score,
                anomaly_status=r.anomaly_status,
                anomaly_severity=r.anomaly_severity,
                sensor=r.sensor,
                timestamp=r.timestamp,
            ))
        anom_count += 1

    db.commit()
    return {"predictions": pred_count, "anomalies": anom_count}
