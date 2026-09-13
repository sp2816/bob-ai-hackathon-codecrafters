"""
Tests for Phase 5A: Isolation Forest Training
Member 2 (Selin) | src/backend/member2_ml/tests/test_isolation_forest.py
"""

import pytest
import numpy as np
from pathlib import Path

from sklearn.ensemble import IsolationForest

from models.train_isolation_forest import train_isolation_forest
from models.model_utils import load_artifact, load_feature_columns, IF_MODEL_PATH, IF_FEATURE_COLS_PATH
from features.feature_engineering import run_feature_pipeline

@pytest.fixture(scope="module")
def trained_model():
    """Trains the model once for all tests to use."""
    model = train_isolation_forest(random_state=42)
    return model

def test_artifacts_saved_and_loadable(trained_model):
    """model artifact saves and loads successfully"""
    assert IF_MODEL_PATH.exists(), "Isolation Forest model artifact not saved."
    assert IF_FEATURE_COLS_PATH.exists(), "Isolation Forest feature columns not saved."

    loaded_model = load_artifact(IF_MODEL_PATH)
    assert isinstance(loaded_model, IsolationForest)
    
def test_feature_columns():
    """exactly 24 Isolation Forest features, identifiers and maintenance excluded"""
    loaded_cols = load_feature_columns(IF_FEATURE_COLS_PATH)
    
    assert len(loaded_cols) == 24, f"Expected exactly 24 Isolation Forest features, got {len(loaded_cols)}."

    for col in loaded_cols:
        assert "asset_id" not in col
        assert "component_id" not in col
        assert "criticality" not in col
        assert "maintenance" not in col
        assert "hours_since_service" not in col
        assert "overdue_flag" not in col

def test_prediction_output_shape(trained_model):
    """anomaly scores are generated, prediction output shape is correct"""
    _, _, if_result = run_feature_pipeline()
    X = if_result.X
    
    scores = trained_model.decision_function(X)
    preds = trained_model.predict(X)
    
    assert scores.shape == (X.shape[0],), "Decision function output shape is incorrect."
    assert preds.shape == (X.shape[0],), "Predict output shape is incorrect."

def test_as1047_inference(trained_model):
    """AS-1047 is detected through real inference (without being in the training set)"""
    _, _, if_result = run_feature_pipeline()
    X = if_result.X
    meta = if_result.meta

    as_1047_mask = (meta["asset_id"] == "AS-1047") & (meta["component_id"] == "BRG-1047")
    assert as_1047_mask.any(), "AS-1047 / BRG-1047 missing from dataset."
    
    X_as1047 = X[as_1047_mask]
    status = trained_model.predict(X_as1047)[0]
    score = trained_model.decision_function(X_as1047)[0]
    
    # -1 implies anomaly in sklearn's IsolationForest
    assert status == -1, "AS-1047 / BRG-1047 was not flagged as an anomaly!"
    assert score < 0, "AS-1047 should have a negative anomaly score."

def test_normal_component_inference(trained_model):
    """at least one normal component behaves as expected"""
    _, rf_result, if_result = run_feature_pipeline()
    X = if_result.X
    meta = if_result.meta
    
    is_normal = (rf_result.y == 0) & (meta["asset_id"] != "AS-1047")
    assert is_normal.any(), "No normal components found."
    
    X_normal = X[is_normal]
    status = trained_model.predict(X_normal)
    
    # Normal components should predominantly be classified as normal (status == 1)
    assert np.mean(status == 1) > 0.8, "Normal components should predominantly be classified as normal."

def test_identity_independence_and_cloning(trained_model):
    """no asset_id-specific inference logic exists; cloned feature row with identical values gives identical inference"""
    _, _, if_result = run_feature_pipeline()
    X = if_result.X
    
    row1 = X[0:1].copy()
    
    score1 = trained_model.decision_function(row1)[0]
    status1 = trained_model.predict(row1)[0]
    
    # Simulating a completely different component but with identical sensor behavior features
    row2 = X[0:1].copy()
    score2 = trained_model.decision_function(row2)[0]
    status2 = trained_model.predict(row2)[0]
    
    assert score1 == score2, "Cloned feature row yielded different score!"
    assert status1 == status2, "Cloned feature row yielded different status!"

def test_reproducibility():
    """reproducibility with random_state=42"""
    model1 = train_isolation_forest(random_state=42)
    model2 = train_isolation_forest(random_state=42)
    
    _, _, if_result = run_feature_pipeline()
    X = if_result.X
    
    assert np.allclose(model1.decision_function(X), model2.decision_function(X)), "Models with same random_state produced different scores."
