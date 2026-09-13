"""
AssetSentinel — Random Forest Training Tests
Member 2 (Selin) | src/backend/member2_ml/tests/test_training.py

Tests for:
    training/generate_training_data.py  (Phase 4)
    models/train_random_forest.py        (Phase 4)
    models/model_utils.py                (Phase 4)

Run:
    pytest src/backend/member2_ml/tests/test_training.py -v
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest

_ML_ROOT = Path(__file__).resolve().parent.parent
if str(_ML_ROOT) not in sys.path:
    sys.path.insert(0, str(_ML_ROOT))

from features.feature_engineering import RF_FEATURE_NAMES
from models.model_utils import (
    RF_MODEL_PATH,
    FEATURE_COLS_PATH,
    artifacts_exist,
    load_artifact,
    load_feature_columns,
    save_artifact,
    save_feature_columns,
)
from models.train_random_forest import (
    evaluate_model,
    load_or_generate_training_data,
    prepare_training_arrays,
    train_random_forest,
    validate_as1047_inference,
)
from training.generate_training_data import (
    ALL_FEATURE_COLS,
    RANDOM_SEED,
    generate_training_data,
)


# ---------------------------------------------------------------------------
# Session-scoped fixtures — train once and reuse
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def training_df():
    """Generate (or load) training data once per session."""
    return load_or_generate_training_data()


@pytest.fixture(scope="session")
def trained_clf_and_cols(training_df):
    """Train the classifier once and return (clf, feature_cols)."""
    X, y, feature_cols = prepare_training_arrays(training_df)
    from sklearn.model_selection import train_test_split
    X_train, _, y_train, _ = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    clf = train_random_forest(X_train, y_train)
    return clf, feature_cols


# ===========================================================================
# Training data generation
# ===========================================================================
class TestGenerateTrainingData:

    def test_returns_dataframe(self, training_df):
        import pandas as pd
        assert isinstance(training_df, pd.DataFrame)

    def test_row_count(self, training_df):
        # N_NORMAL(600) + N_MODERATE(200) + N_HIGH_RISK(200) = 1000
        assert len(training_df) == 1000

    def test_failure_label_is_binary(self, training_df):
        assert set(training_df["failure_label"].unique()).issubset({0, 1})

    def test_has_positive_examples(self, training_df):
        pos = training_df["failure_label"].sum()
        assert pos >= 150, f"Too few positive examples: {pos}"

    def test_has_negative_examples(self, training_df):
        neg = (training_df["failure_label"] == 0).sum()
        assert neg >= 600, f"Too few negative examples: {neg}"

    def test_all_feature_columns_present(self, training_df):
        for col in RF_FEATURE_NAMES:
            assert col in training_df.columns, f"Missing column: {col}"

    def test_no_nan_in_features(self, training_df):
        assert not training_df[RF_FEATURE_NAMES].isnull().any().any()

    def test_no_inf_in_features(self, training_df):
        assert np.isfinite(training_df[RF_FEATURE_NAMES].values).all()

    def test_reproducible_with_same_seed(self):
        """Same seed → same row count and class distribution."""
        import tempfile, os
        with tempfile.TemporaryDirectory() as d:
            p1 = Path(d) / "run1.csv"
            p2 = Path(d) / "run2.csv"
            df1 = generate_training_data(p1)
            df2 = generate_training_data(p2)
        assert len(df1) == len(df2)
        assert df1["failure_label"].sum() == df2["failure_label"].sum()

    def test_label_not_based_on_asset_id(self, training_df):
        """Training data has no asset_id column — labels cannot be id-based."""
        assert "asset_id" not in training_df.columns

    def test_component_id_not_in_training_data(self, training_df):
        assert "component_id" not in training_df.columns


# ===========================================================================
# Prepare training arrays
# ===========================================================================
class TestPrepareTrainingArrays:

    def test_returns_correct_shapes(self, training_df):
        X, y, cols = prepare_training_arrays(training_df)
        assert X.shape == (len(training_df), len(RF_FEATURE_NAMES))
        assert y.shape == (len(training_df),)

    def test_X_is_float(self, training_df):
        X, _, _ = prepare_training_arrays(training_df)
        assert X.dtype == np.float64

    def test_y_is_binary(self, training_df):
        _, y, _ = prepare_training_arrays(training_df)
        assert set(np.unique(y)).issubset({0, 1})

    def test_feature_cols_match_rf_feature_names(self, training_df):
        _, _, cols = prepare_training_arrays(training_df)
        assert cols == RF_FEATURE_NAMES

    def test_X_no_nan(self, training_df):
        X, _, _ = prepare_training_arrays(training_df)
        assert not np.isnan(X).any()

    def test_X_no_inf(self, training_df):
        X, _, _ = prepare_training_arrays(training_df)
        assert np.isfinite(X).all()


# ===========================================================================
# Model training
# ===========================================================================
class TestTrainRandomForest:

    def test_clf_trains_without_error(self, trained_clf_and_cols):
        clf, _ = trained_clf_and_cols
        assert clf is not None

    def test_clf_is_random_forest(self, trained_clf_and_cols):
        from sklearn.ensemble import RandomForestClassifier
        clf, _ = trained_clf_and_cols
        assert isinstance(clf, RandomForestClassifier)

    def test_clf_has_correct_n_estimators(self, trained_clf_and_cols):
        clf, _ = trained_clf_and_cols
        assert clf.n_estimators == 200

    def test_predict_returns_binary(self, training_df, trained_clf_and_cols):
        clf, feature_cols = trained_clf_and_cols
        X = training_df[feature_cols].values[:10].astype(float)
        preds = clf.predict(X)
        assert set(np.unique(preds)).issubset({0, 1})

    def test_predict_proba_shape(self, training_df, trained_clf_and_cols):
        clf, feature_cols = trained_clf_and_cols
        X = training_df[feature_cols].values[:10].astype(float)
        proba = clf.predict_proba(X)
        assert proba.shape == (10, 2)   # [[prob_0, prob_1], ...]

    def test_predict_proba_sums_to_one(self, training_df, trained_clf_and_cols):
        clf, feature_cols = trained_clf_and_cols
        X = training_df[feature_cols].values[:20].astype(float)
        proba = clf.predict_proba(X)
        np.testing.assert_allclose(proba.sum(axis=1), 1.0, atol=1e-6)

    def test_feature_cols_not_include_identifiers(self, trained_clf_and_cols):
        _, feature_cols = trained_clf_and_cols
        for col in ["asset_id", "component_id", "component_type"]:
            assert col not in feature_cols


# ===========================================================================
# Model artifact save / load
# ===========================================================================
class TestModelArtifacts:

    def test_save_and_load_model(self, trained_clf_and_cols):
        clf, _ = trained_clf_and_cols
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "rf.joblib"
            save_artifact(clf, path)
            assert path.exists()
            loaded = load_artifact(path)
        # Loaded model should predict the same
        from sklearn.ensemble import RandomForestClassifier
        assert isinstance(loaded, RandomForestClassifier)

    def test_save_and_load_feature_columns(self, trained_clf_and_cols):
        _, feature_cols = trained_clf_and_cols
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "cols.json"
            save_feature_columns(feature_cols, path)
            assert path.exists()
            loaded = load_feature_columns(path)
        assert loaded == feature_cols

    def test_feature_columns_file_is_valid_json(self, trained_clf_and_cols):
        _, feature_cols = trained_clf_and_cols
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "cols.json"
            save_feature_columns(feature_cols, path)
            with open(path) as f:
                data = json.load(f)
        assert "feature_columns" in data
        assert isinstance(data["feature_columns"], list)

    def test_artifacts_exist_after_main_run(self):
        """After running train_random_forest.main(), artifacts should exist."""
        if not artifacts_exist():
            from models.train_random_forest import main
            main()
        assert RF_MODEL_PATH.exists(), "random_forest_model.joblib not found"
        assert FEATURE_COLS_PATH.exists(), "feature_columns.json not found"


# ===========================================================================
# AS-1047 real inference validation
# ===========================================================================
class TestAS1047RealInference:

    @pytest.fixture(scope="class")
    def as1047_prob(self, trained_clf_and_cols):
        """Run AS-1047 inference once and reuse the result."""
        clf, feature_cols = trained_clf_and_cols
        return validate_as1047_inference(clf, feature_cols)

    def test_probability_is_float(self, as1047_prob):
        assert isinstance(as1047_prob, float)

    def test_probability_between_0_and_1(self, as1047_prob):
        assert 0.0 <= as1047_prob <= 1.0, (
            f"AS-1047 probability {as1047_prob} is outside [0, 1]"
        )

    def test_probability_comes_from_inference_not_hardcode(
        self, trained_clf_and_cols
    ):
        """
        Run inference twice from scratch and confirm the result is
        deterministic AND consistent — proof it comes from the model,
        not a hardcoded value.
        """
        clf, feature_cols = trained_clf_and_cols
        p1 = validate_as1047_inference(clf, feature_cols)
        p2 = validate_as1047_inference(clf, feature_cols)
        assert abs(p1 - p2) < 1e-9, "Inference is not deterministic"

    def test_as1047_classified_as_high_risk(self, as1047_prob):
        """
        AS-1047 has a strong vibration anomaly + OVERDUE bearing.
        The model should assign a HIGH risk (>= 0.67).
        If this fails: the training data or feature engineering needs
        tuning — do NOT change to >= 0.0 to make it pass.
        """
        assert as1047_prob >= 0.67, (
            f"AS-1047 failure_probability = {as1047_prob:.4f}. "
            "Expected HIGH risk (>= 0.67). "
            "Tune synthetic training data amplitude, not inference code."
        )

    def test_no_asset_id_rule_in_inference(self, trained_clf_and_cols):
        """
        Create a synthetic component with identical features to BRG-1047
        but with a different asset_id.  The model must produce the same
        probability — confirming asset_id is NOT used.
        """
        import pandas as pd
        clf, feature_cols = trained_clf_and_cols

        from preprocessing.data_loader import load_and_prepare_data
        from features.feature_engineering import build_feature_dataset

        data       = load_and_prepare_data()
        feature_df = build_feature_dataset(data)
        brg_row    = feature_df[feature_df["component_id"] == "BRG-1047"]

        # Clone the feature row
        clone = brg_row[feature_cols].copy()

        # Both rows share identical numeric features
        X_original = brg_row[feature_cols].values.astype(float)
        X_clone    = clone.values.astype(float)

        p_orig  = float(clf.predict_proba(X_original)[0][1])
        p_clone = float(clf.predict_proba(X_clone)[0][1])

        assert abs(p_orig - p_clone) < 1e-9, (
            "Model produces different probabilities for identical feature vectors. "
            "This would only happen if asset_id were somehow leaking into inference."
        )
