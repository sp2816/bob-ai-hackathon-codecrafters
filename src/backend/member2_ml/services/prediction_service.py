"""
AssetSentinel — ML Prediction Service
Member 2 (Selin) | src/backend/member2_ml/services/prediction_service.py

Purpose:
    Provides a reusable, independent Python interface for ML predictions.
    Computes failure probability and anomaly status per component.
    Determines anomaly severity and identifies the anomalous sensor.

Architecture constraints:
    - NO FastAPI or HTTP logic
    - NO Database logic
    - NO Readiness or Mission scoring
    - Models are loaded once and cached (no retraining)
"""

import uuid
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Literal
import pandas as pd
import numpy as np

from features.feature_engineering import run_feature_pipeline
from models.model_utils import (
    load_artifact, 
    load_feature_columns, 
    RF_MODEL_PATH, 
    FEATURE_COLS_PATH, 
    IF_MODEL_PATH, 
    IF_FEATURE_COLS_PATH
)

@dataclass
class ComponentPredictionResult:
    prediction_id: str
    asset_id: str
    component_id: str
    failure_probability: float
    risk_category: Literal["LOW", "MEDIUM", "HIGH"]
    anomaly_score: float
    anomaly_status: Literal["NORMAL", "HIGH"]
    anomaly_severity: Literal["LOW", "MEDIUM", "HIGH"]
    sensor: Literal["vibration", "temperature", "pressure", "RPM", "NONE"]
    timestamp: str

# --- Deterministic Rules Configuration ---
RISK_CATEGORY_THRESHOLDS = {
    "MEDIUM": 0.35,
    "HIGH": 0.67
}

SENSOR_SCORE_WEIGHTS = {
    "max_z_score": 1.0,
    "abs_trend_slope": 0.0,
    "relative_deviation": 0.5
}

SEVERITY_THRESHOLDS = {
    "MEDIUM": 2.0,
    "HIGH": 3.0
}

SUPPORTED_SENSORS = ["vibration", "temperature", "pressure", "RPM"]
# -----------------------------------------

class MLPredictionService:
    """
    Stateful service that caches ML models in memory to avoid repeated disk reads.
    """
    def __init__(self):
        self._rf_model = None
        self._rf_cols = None
        self._if_model = None
        self._if_cols = None

    def _ensure_models_loaded(self):
        """Loads models if they are not already cached. Raises descriptive errors."""
        try:
            if self._rf_model is None or self._rf_cols is None:
                self._rf_model = load_artifact(RF_MODEL_PATH)
                self._rf_cols = load_feature_columns(FEATURE_COLS_PATH)
            
            if self._if_model is None or self._if_cols is None:
                self._if_model = load_artifact(IF_MODEL_PATH)
                self._if_cols = load_feature_columns(IF_FEATURE_COLS_PATH)
        except FileNotFoundError as e:
            raise RuntimeError(f"Model artifacts missing. Ensure training has run. Details: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to load model artifacts. Details: {e}")

    def _map_risk_category(self, prob: float) -> Literal["LOW", "MEDIUM", "HIGH"]:
        if prob >= RISK_CATEGORY_THRESHOLDS["HIGH"]:
            return "HIGH"
        if prob >= RISK_CATEGORY_THRESHOLDS["MEDIUM"]:
            return "MEDIUM"
        return "LOW"

    def _map_anomaly_status(self, if_prediction: int) -> Literal["NORMAL", "HIGH"]:
        return "HIGH" if if_prediction == -1 else "NORMAL"

    def _calculate_sensor_score(self, row: pd.Series, sensor: str) -> float:
        """Deterministically scores how abnormal a specific sensor is."""
        z_score = row.get(f"{sensor}__max_z_score", 0.0)
        trend = abs(row.get(f"{sensor}__trend_slope", 0.0))
        latest = row.get(f"{sensor}__latest_value", 0.0)
        mean = row.get(f"{sensor}__rolling_mean", 0.0)
        
        # Relative deviation percentage heavily penalizes proportional spikes
        relative_dev = (abs(latest - mean) / (abs(mean) + 1e-6)) * 100.0
        
        score = (
            z_score * SENSOR_SCORE_WEIGHTS["max_z_score"] +
            trend * SENSOR_SCORE_WEIGHTS["abs_trend_slope"] +
            relative_dev * SENSOR_SCORE_WEIGHTS["relative_deviation"]
        )
        return float(score)

    def _map_severity(self, status: str, max_sensor_score: float) -> Literal["LOW", "MEDIUM", "HIGH"]:
        if status == "NORMAL":
            return "LOW"
        if max_sensor_score >= SEVERITY_THRESHOLDS["HIGH"]:
            return "HIGH"
        if max_sensor_score >= SEVERITY_THRESHOLDS["MEDIUM"]:
            return "MEDIUM"
        return "LOW"

    def predict_all_components(self) -> list[ComponentPredictionResult]:
        """
        Executes real inference on all components using existing engineered features.
        """
        self._ensure_models_loaded()
        
        # 1. Get engineered features via existing pipeline
        try:
            feature_df, rf_result, if_result = run_feature_pipeline()
        except Exception as e:
            raise RuntimeError(f"Failed to run feature engineering pipeline. Details: {e}")
            
        if len(feature_df) == 0:
            raise ValueError("Feature dataset is empty.")

        # 2. Check for NaN/Inf in inputs
        if rf_result.X is None or if_result.X is None:
            raise ValueError("Feature matrix is missing.")
        if np.isnan(rf_result.X).any() or np.isinf(rf_result.X).any():
            raise ValueError("NaN or Infinite values detected in Random Forest inputs.")
        if np.isnan(if_result.X).any() or np.isinf(if_result.X).any():
            raise ValueError("NaN or Infinite values detected in Isolation Forest inputs.")

        # 3. Verify feature column orders
        if list(rf_result.feature_names) != self._rf_cols:
            raise ValueError("Random Forest feature columns do not match training order.")
        if list(if_result.feature_names) != self._if_cols:
            raise ValueError("Isolation Forest feature columns do not match training order.")
            
        # 4. Perform Inference (Real Inference)
        # Random Forest failure probability
        rf_probs = self._rf_model.predict_proba(rf_result.X)[:, 1]
        
        # Isolation Forest anomaly score and status
        if_scores = self._if_model.decision_function(if_result.X)
        if_preds = self._if_model.predict(if_result.X)

        results = []
        current_time = datetime.now(timezone.utc).isoformat()
        
        for i in range(len(feature_df)):
            row = feature_df.iloc[i]
            asset_id = row["asset_id"]
            component_id = row["component_id"]
            
            # Identifiers must NEVER be used as ML inputs. 
            # We explicitly ran prediction on rf_result.X / if_result.X which lack identifiers.
            
            prob = float(rf_probs[i])
            risk_category = self._map_risk_category(prob)
            
            anomaly_score = float(if_scores[i])
            anomaly_status = self._map_anomaly_status(if_preds[i])
            
            # Anomaly Sensor & Severity Logic
            if anomaly_status == "NORMAL":
                sensor = "NONE"
                anomaly_severity = "LOW"
            else:
                sensor_scores = {
                    s: self._calculate_sensor_score(row, s) 
                    for s in SUPPORTED_SENSORS
                }
                sensor = max(sensor_scores.items(), key=lambda x: x[1])[0]
                anomaly_severity = self._map_severity(anomaly_status, sensor_scores[sensor])

            prediction_id = f"PRED-{uuid.uuid4().hex[:8].upper()}"

            results.append(ComponentPredictionResult(
                prediction_id=prediction_id,
                asset_id=str(asset_id),
                component_id=str(component_id),
                failure_probability=prob,
                risk_category=risk_category,
                anomaly_score=anomaly_score,
                anomaly_status=anomaly_status,
                anomaly_severity=anomaly_severity,
                sensor=sensor,
                timestamp=current_time
            ))

        return results

    def get_component_prediction(self, asset_id: str, component_id: str) -> ComponentPredictionResult:
        """Retrieves prediction for a single specified component."""
        if not asset_id or not component_id:
            raise ValueError("asset_id and component_id must be provided.")
            
        all_results = self.predict_all_components()
        for res in all_results:
            if res.asset_id == asset_id and res.component_id == component_id:
                return res
                
        raise ValueError(f"Component not found: asset_id={asset_id}, component_id={component_id}")

# Expose singleton-like convenient functions
_instance = MLPredictionService()

def predict_all_components() -> list[ComponentPredictionResult]:
    return _instance.predict_all_components()

def get_component_prediction(asset_id: str, component_id: str) -> ComponentPredictionResult:
    return _instance.get_component_prediction(asset_id, component_id)
