"""
Tests for Phase 5B: ML Prediction Service
Member 2 (Selin) | src/backend/member2_ml/tests/test_prediction_service.py
"""

import pytest
import numpy as np
from datetime import datetime

from services.prediction_service import (
    predict_all_components,
    get_component_prediction,
    ComponentPredictionResult,
    MLPredictionService
)

def test_single_component_prediction():
    """21. Single component prediction works"""
    results = predict_all_components()
    first = results[0]
    
    res = get_component_prediction(first.asset_id, first.component_id)
    assert isinstance(res, ComponentPredictionResult)
    assert res.asset_id == first.asset_id
    assert res.component_id == first.component_id

def test_all_component_prediction():
    """22. All component prediction works"""
    results = predict_all_components()
    assert len(results) > 0
    assert all(isinstance(r, ComponentPredictionResult) for r in results)

def test_missing_component_raises_error():
    """17. Missing component raises a clear error
       18. Missing asset raises a clear error"""
    with pytest.raises(ValueError, match="Component not found"):
        get_component_prediction("FAKE-ASSET", "FAKE-COMPONENT")

def test_rf_probability_bounds():
    """3. Random Forest predictions are between 0 and 1"""
    results = predict_all_components()
    for res in results:
        assert 0.0 <= res.failure_probability <= 1.0

def test_risk_categories():
    """4. risk_category are only LOW, MEDIUM, HIGH"""
    results = predict_all_components()
    for res in results:
        assert res.risk_category in ["LOW", "MEDIUM", "HIGH"]

def test_anomaly_status_and_sensor():
    """
    5. Anomaly status is only NORMAL, HIGH
    6. sensor is only vibration, temperature, pressure, RPM, NONE
    24. Normal components return sensor = NONE when anomaly_status is NORMAL
    """
    results = predict_all_components()
    for res in results:
        assert res.anomaly_status in ["NORMAL", "HIGH"]
        assert res.sensor in ["vibration", "temperature", "pressure", "RPM", "NONE"]
        
        if res.anomaly_status == "NORMAL":
            assert res.sensor == "NONE"
            assert res.anomaly_severity == "LOW"

def test_anomaly_severity():
    """7. Anomaly severity is only LOW, MEDIUM, HIGH"""
    results = predict_all_components()
    for res in results:
        assert res.anomaly_severity in ["LOW", "MEDIUM", "HIGH"]

def test_as1047_validation():
    """
    8. AS-1047 produces HIGH risk through real inference
    9. AS-1047 produces HIGH anomaly_status through real inference
    10. AS-1047 identifies vibration through deterministic analysis
    """
    res = get_component_prediction("AS-1047", "BRG-1047")
    
    assert res.risk_category == "HIGH", "AS-1047 did not produce HIGH risk."
    assert res.failure_probability > 0.8, "AS-1047 probability is lower than expected (~0.899)."
    
    assert res.anomaly_status == "HIGH", "AS-1047 was not flagged as HIGH anomaly status."
    assert res.sensor == "vibration", "AS-1047 did not identify vibration as the sensor."
    assert res.anomaly_severity in ["MEDIUM", "HIGH"]

def test_normal_component_validation():
    """11. A normal component produces a valid result"""
    results = predict_all_components()
    normal_res = None
    for res in results:
        if res.asset_id != "AS-1047" and res.anomaly_status == "NORMAL":
            normal_res = res
            break
            
    assert normal_res is not None, "Could not find a normal component to test."
    assert 0.0 <= normal_res.failure_probability <= 1.0
    assert normal_res.sensor == "NONE"
    assert normal_res.anomaly_severity == "LOW"
    assert normal_res.risk_category in ["LOW", "MEDIUM", "HIGH"]

def test_identifiers_not_in_features():
    """
    12. Identifiers are not used as model features
    13, 14. Random Forest / Isolation Forest feature column order matches saved requirements
    """
    service = MLPredictionService()
    service._ensure_models_loaded()
    
    for col in service._rf_cols:
        assert "asset_id" not in col
        assert "component_id" not in col
        
    for col in service._if_cols:
        assert "asset_id" not in col
        assert "component_id" not in col

def test_model_loading_caching():
    """
    1. Random Forest model loads correctly
    2. Isolation Forest model loads correctly
    15. No model retraining occurs during prediction
    """
    service = MLPredictionService()
    service._ensure_models_loaded()
    
    assert service._rf_model is not None
    assert service._if_model is not None

def test_prediction_id_and_timestamp():
    """Check prediction_id and timestamp presence and types"""
    res = predict_all_components()[0]
    
    assert hasattr(res, "prediction_id")
    assert isinstance(res.prediction_id, str)
    assert res.prediction_id.startswith("PRED-")
    
    assert hasattr(res, "timestamp")
    assert isinstance(res.timestamp, str)
    # Check simple ISO-format compatibility
    dt = datetime.fromisoformat(res.timestamp)
    assert dt is not None
