"""
AssetSentinel — Single-Component ML Inference
src/backend/member2_ml/services/single_component_inference.py

Purpose:
    Provides deterministic, single-component ML inference for the Add Asset
    workflow. This complements (but does NOT modify) the existing
    predict_all_components() fleet-wide pipeline.

Architecture position:
    Add Asset API
        → predict_single_component_asset()     ← THIS FILE
        → run_feature_pipeline(data=...)        (in-memory, no CSV read)
        → rf_model.predict_proba()              (single row)
        → if_model.predict()                    (single row)
        → ComponentPredictionResult

Design constraints:
    - DOES NOT modify prediction_service.py
    - DOES NOT re-run fleet-wide inference
    - DOES NOT use randomness (np.linspace only — same inputs = same output)
    - Uses the SAME trained model artifacts and feature pipeline as the fleet run
    - Sensor windows are labeled as synthetic condition profiles, not historical telemetry
"""

from __future__ import annotations

import logging
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Add member2_ml root to sys.path so imports work from any caller location
# ---------------------------------------------------------------------------
_MEMBER2_ROOT = Path(__file__).resolve().parents[1]
if str(_MEMBER2_ROOT) not in sys.path:
    sys.path.insert(0, str(_MEMBER2_ROOT))

from features.feature_engineering import run_feature_pipeline
from models.model_utils import (
    load_artifact,
    load_feature_columns,
    RF_MODEL_PATH,
    FEATURE_COLS_PATH,
    IF_MODEL_PATH,
    IF_FEATURE_COLS_PATH,
)
from preprocessing.data_loader import PreparedDatasets
from services.prediction_service import ComponentPredictionResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Risk / severity constants — must match prediction_service.py exactly
# ---------------------------------------------------------------------------
_RISK_THRESHOLDS = {"MEDIUM": 0.35, "HIGH": 0.67}
_SEVERITY_THRESHOLDS = {"MEDIUM": 2.0, "HIGH": 3.0}
_SENSOR_SCORE_WEIGHTS = {"max_z_score": 1.0, "abs_trend_slope": 0.0, "relative_deviation": 0.5}
_SUPPORTED_SENSORS = ["vibration", "temperature", "pressure", "RPM"]

# ---------------------------------------------------------------------------
# Deterministic sensor condition profiles
#
# These represent plausible operating ranges validated against the training
# dataset distribution. They are NOT historical telemetry — they are
# explicit synthetic condition profiles chosen by the operator.
#
# baseline = center of the profile's typical operating range
# std      = within-profile variability (used to compute z-scores)
# ---------------------------------------------------------------------------
SENSOR_PROFILES: dict[str, dict[str, dict[str, float]]] = {
    "NORMAL": {
        "vibration":   {"baseline": 3.0,   "std": 0.5},
        "temperature": {"baseline": 75.0,  "std": 3.0},
        "pressure":    {"baseline": 100.0, "std": 5.0},
        "RPM":         {"baseline": 2800.0, "std": 100.0},
    },
    "DEGRADING": {
        "vibration":   {"baseline": 5.5,   "std": 0.8},
        "temperature": {"baseline": 86.0,  "std": 4.0},
        "pressure":    {"baseline": 83.0,  "std": 6.0},
        "RPM":         {"baseline": 2400.0, "std": 150.0},
    },
    "CRITICAL": {
        "vibration":   {"baseline": 9.5,   "std": 1.5},
        "temperature": {"baseline": 98.0,  "std": 5.0},
        "pressure":    {"baseline": 65.0,  "std": 8.0},
        "RPM":         {"baseline": 1800.0, "std": 200.0},
    },
}

# Number of synthetic readings — must equal ROLLING_WINDOW (20) in feature_engineering.py
_N_READINGS = 20

# ---------------------------------------------------------------------------
# Module-level model cache (loaded once, reused across requests)
# ---------------------------------------------------------------------------
_rf_model = None
_rf_cols: list[str] | None = None
_if_model = None
_if_cols: list[str] | None = None


def _ensure_models_loaded() -> None:
    """Load trained model artifacts once and cache them for subsequent calls."""
    global _rf_model, _rf_cols, _if_model, _if_cols
    if _rf_model is None:
        logger.info("[single_inference] Loading model artifacts…")
        _rf_model = load_artifact(RF_MODEL_PATH)
        _rf_cols = load_feature_columns(FEATURE_COLS_PATH)
        _if_model = load_artifact(IF_MODEL_PATH)
        _if_cols = load_feature_columns(IF_FEATURE_COLS_PATH)
        logger.info("[single_inference] Models loaded. RF cols: %d | IF cols: %d",
                    len(_rf_cols), len(_if_cols))


# ---------------------------------------------------------------------------
# Deterministic sensor window builder
# ---------------------------------------------------------------------------

def build_deterministic_sensor_window(
    asset_id: str,
    component_id: str,
    sensor_values: dict[str, float],
    condition: str,
) -> pd.DataFrame:
    """
    Build a deterministic synthetic observation window for ML feature engineering.

    Strategy:
        - Uses np.linspace() from the profile baseline to the operator-provided
          current value across _N_READINGS readings.
        - NO randomness — identical inputs produce identical windows every run.
        - Labeled clearly as a synthetic condition profile in the UI.

    The resulting DataFrame feeds directly into engineer_sensor_features(),
    which computes the z-scores, rolling stats, and trend slopes the models need.

    Args:
        asset_id:      Asset identifier
        component_id:  Component identifier
        sensor_values: Dict mapping sensor_type → current operator-entered value
        condition:     "NORMAL" | "DEGRADING" | "CRITICAL"

    Returns:
        pd.DataFrame with columns: sensor_id, asset_id, component_id,
                                   timestamp, sensor_type, value
    """
    if condition not in SENSOR_PROFILES:
        raise ValueError(
            f"Unknown sensor condition: '{condition}'. "
            f"Allowed: {list(SENSOR_PROFILES.keys())}"
        )

    profile = SENSOR_PROFILES[condition]
    records: list[dict] = []
    base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)

    for sensor_type, current_value in sensor_values.items():
        if sensor_type not in profile:
            raise ValueError(f"Unsupported sensor type: '{sensor_type}'")

        baseline = profile[sensor_type]["baseline"]
        # Linear progression: historical baseline → operator's current value
        # Deterministic: np.linspace produces identical output for identical inputs
        hist_values = np.linspace(baseline, float(current_value), _N_READINGS)

        for j, val in enumerate(hist_values):
            ts = base_time + timedelta(hours=j)
            records.append({
                "sensor_id":    f"SYN-{asset_id}-{sensor_type[:3].upper()}-{j:04d}",
                "asset_id":     asset_id,
                "component_id": component_id,
                "timestamp":    ts.isoformat(),
                "sensor_type":  sensor_type,
                "value":        float(val),
            })

    logger.debug("[single_inference] Built %d synthetic sensor readings for %s/%s",
                 len(records), asset_id, component_id)
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Internal helper — build components DataFrame row
# ---------------------------------------------------------------------------

def _build_component_df(
    asset_id: str,
    component_id: str,
    component_type: str,
    criticality: str,
    operating_hours: float,
    life_limit: float | None,
    service_interval_hours: float,
    hours_at_last_service: float,
    installation_date: str | None,
) -> pd.DataFrame:
    return pd.DataFrame([{
        "component_id":          component_id,
        "asset_id":              asset_id,
        "component_type":        component_type,
        "criticality":           criticality,
        "installation_date":     installation_date or "2024-01-01",
        "operating_hours":       float(operating_hours),
        "life_limit":            float(life_limit) if life_limit else float(operating_hours) * 2,
        "service_interval_hours": float(service_interval_hours),
        "hours_at_last_service": float(hours_at_last_service),
    }])


# ---------------------------------------------------------------------------
# Scoring helpers (replicated from prediction_service.py for independence)
# ---------------------------------------------------------------------------

def _map_risk_category(prob: float) -> Literal["LOW", "MEDIUM", "HIGH"]:
    if prob >= _RISK_THRESHOLDS["HIGH"]:
        return "HIGH"
    if prob >= _RISK_THRESHOLDS["MEDIUM"]:
        return "MEDIUM"
    return "LOW"


def _map_anomaly_status(if_prediction: int) -> Literal["NORMAL", "HIGH"]:
    return "HIGH" if if_prediction == -1 else "NORMAL"


def _calculate_sensor_score(row: pd.Series, sensor: str) -> float:
    z_score = row.get(f"{sensor}__max_z_score", 0.0)
    trend = abs(row.get(f"{sensor}__trend_slope", 0.0))
    latest = row.get(f"{sensor}__latest_value", 0.0)
    mean = row.get(f"{sensor}__rolling_mean", 0.0)
    relative_dev = (abs(latest - mean) / (abs(mean) + 1e-6)) * 100.0
    return float(
        z_score * _SENSOR_SCORE_WEIGHTS["max_z_score"]
        + trend * _SENSOR_SCORE_WEIGHTS["abs_trend_slope"]
        + relative_dev * _SENSOR_SCORE_WEIGHTS["relative_deviation"]
    )


def _map_severity(
    status: str, max_sensor_score: float
) -> Literal["LOW", "MEDIUM", "HIGH"]:
    if status == "NORMAL":
        return "LOW"
    if max_sensor_score >= _SEVERITY_THRESHOLDS["HIGH"]:
        return "HIGH"
    if max_sensor_score >= _SEVERITY_THRESHOLDS["MEDIUM"]:
        return "MEDIUM"
    return "LOW"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def predict_single_component_asset(
    asset_id: str,
    component_id: str,
    component_type: str,
    criticality: str,
    operating_hours: float,
    life_limit: float | None,
    service_interval_hours: float,
    hours_since_service: float,
    sensor_values: dict[str, float],
    condition: str,
) -> ComponentPredictionResult:
    """
    Perform real ML inference for a single new component without running the
    fleet-wide pipeline.

    Uses the same trained RF + IF model artifacts as predict_all_components(),
    but constructs the feature matrix in-memory from operator-provided data.
    No CSV read. No fleet rerun. Deterministic: same inputs → same prediction.

    Args:
        asset_id:              New asset identifier
        component_id:          New component identifier
        component_type:        e.g. "main_bearing", "engine"
        criticality:           "LOW" | "MEDIUM" | "HIGH"
        operating_hours:       Total operating hours of the asset
        life_limit:            Component life limit (hours), optional
        service_interval_hours: Hours between required services
        hours_since_service:   Hours elapsed since last service
        sensor_values:         Dict of current sensor readings
                               {"vibration": float, "temperature": float,
                                "pressure": float, "RPM": float}
        condition:             Synthetic condition profile: "NORMAL" | "DEGRADING" | "CRITICAL"

    Returns:
        ComponentPredictionResult — identical schema as fleet-wide inference output
    """
    _ensure_models_loaded()

    hours_at_last_service = max(0.0, operating_hours - hours_since_service)

    # 1. Build in-memory PreparedDatasets (single component only)
    sensor_df = build_deterministic_sensor_window(asset_id, component_id, sensor_values, condition)
    comp_df = _build_component_df(
        asset_id, component_id, component_type, criticality,
        operating_hours, life_limit, service_interval_hours, hours_at_last_service,
        installation_date=None,
    )
    asset_df = pd.DataFrame([{
        "asset_id":          asset_id,
        "asset_name":        asset_id,
        "asset_type":        "asset",
        "unit":              "NEW",
        "operational_hours": float(operating_hours),
        "current_status":    "UNKNOWN",
    }])
    # Minimal maintenance DF for referential integrity validation (not used by features)
    maint_df = pd.DataFrame([{
        "maintenance_id":    f"MNT-INIT-{component_id}",
        "asset_id":          asset_id,
        "component_id":      component_id,
        "maintenance_type":  "inspection",
        "maintenance_date":  "2024-01-01",
        "technician_action": "Initial synthetic record",
        "status":            "COMPLETED",
        "notes":             "",
    }])

    data = PreparedDatasets(
        assets=asset_df,
        components=comp_df,
        sensors=sensor_df,
        maintenance=maint_df,
    )

    # 2. Run feature pipeline on this single-component in-memory dataset
    try:
        feature_df, rf_result, if_result = run_feature_pipeline(data=data)
    except Exception as e:
        raise RuntimeError(
            f"Feature pipeline failed for single-component inference "
            f"({asset_id}/{component_id}): {e}"
        ) from e

    if len(feature_df) == 0:
        raise ValueError(
            f"Feature pipeline produced empty dataset for {asset_id}/{component_id}. "
            "Check that sensor readings are present for all sensor types."
        )

    # 3. Verify feature column order matches training artifacts
    if list(rf_result.feature_names) != _rf_cols:
        raise ValueError(
            f"RF feature column mismatch. "
            f"Expected {len(_rf_cols)} cols, got {len(rf_result.feature_names)}. "
            "Ensure the same RF_FEATURE_NAMES constant is used."
        )
    if list(if_result.feature_names) != _if_cols:
        raise ValueError(
            f"IF feature column mismatch. "
            f"Expected {len(_if_cols)} cols, got {len(if_result.feature_names)}."
        )

    # 4. Single-row inference using trained models
    import numpy as _np
    if _np.isnan(rf_result.X).any() or _np.isinf(rf_result.X).any():
        raise ValueError("NaN/Inf detected in RF feature matrix. Check sensor input values.")
    if _np.isnan(if_result.X).any() or _np.isinf(if_result.X).any():
        raise ValueError("NaN/Inf detected in IF feature matrix. Check sensor input values.")

    rf_prob     = float(_rf_model.predict_proba(rf_result.X)[0, 1])
    if_score    = float(_if_model.decision_function(if_result.X)[0])
    if_pred_val = int(_if_model.predict(if_result.X)[0])

    risk_category  = _map_risk_category(rf_prob)
    anomaly_status = _map_anomaly_status(if_pred_val)

    # 5. Anomaly sensor & severity
    row = feature_df.iloc[0]
    if anomaly_status == "NORMAL":
        top_sensor      = "NONE"
        anomaly_severity = "LOW"
    else:
        sensor_scores = {s: _calculate_sensor_score(row, s) for s in _SUPPORTED_SENSORS}
        top_sensor    = max(sensor_scores.items(), key=lambda x: x[1])[0]
        anomaly_severity = _map_severity(anomaly_status, sensor_scores[top_sensor])

    prediction_id = f"PRED-{uuid.uuid4().hex[:8].upper()}"
    timestamp     = datetime.now(timezone.utc).isoformat()

    logger.info(
        "[single_inference] %s/%s → prob=%.3f risk=%s anomaly=%s severity=%s",
        asset_id, component_id, rf_prob, risk_category, anomaly_status, anomaly_severity,
    )

    return ComponentPredictionResult(
        prediction_id=prediction_id,
        asset_id=asset_id,
        component_id=component_id,
        failure_probability=rf_prob,
        risk_category=risk_category,
        anomaly_score=if_score,
        anomaly_status=anomaly_status,
        anomaly_severity=anomaly_severity,
        sensor=top_sensor,
        timestamp=timestamp,
    )
