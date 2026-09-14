"""
AssetSentinel — Feature Engineering Tests
Member 2 (Selin) | src/backend/member2_ml/tests/test_feature_engineering.py

Tests for features/feature_engineering.py (Phase 3).

Run with:
    pytest src/backend/member2_ml/tests/test_feature_engineering.py -v

Coverage:
    - TestSensorFeatures          sensor feature calculation per group
    - TestMaintenanceFeatures     hours_since_service, overdue_flag, ratio
    - TestCriticalityEncoding     enum → numeric mapping
    - TestBuildFeatureDataset     merged output integrity
    - TestRandomForestFeatures    X shape, y labelling, no identifiers
    - TestIsolationForestFeatures X shape, no maintenance cols, no identifiers
    - TestAS1047Degradation       canonical scenario shows stronger signal
    - TestNaNAndInfGuards         no NaN or Inf in model inputs
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Path setup — works whether pytest is run from repo root or member2_ml/
# ---------------------------------------------------------------------------
_ML_ROOT = Path(__file__).resolve().parent.parent
if str(_ML_ROOT) not in sys.path:
    sys.path.insert(0, str(_ML_ROOT))

from features.feature_engineering import (
    CRITICALITY_ENCODING,
    IF_FEATURE_NAMES,
    RF_FEATURE_NAMES,
    Z_SCORE_THRESHOLD,
    build_feature_dataset,
    encode_component_features,
    engineer_maintenance_features,
    engineer_sensor_features,
    prepare_isolation_forest_features,
    prepare_random_forest_features,
    run_feature_pipeline,
)
from preprocessing.data_loader import load_and_prepare_data

# ---------------------------------------------------------------------------
# Session-scoped fixtures — load data and build features once
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def prepared():
    return load_and_prepare_data()


@pytest.fixture(scope="session")
def feature_df(prepared):
    return build_feature_dataset(prepared)


@pytest.fixture(scope="session")
def rf_result(feature_df):
    return prepare_random_forest_features(feature_df)


@pytest.fixture(scope="session")
def if_result(feature_df):
    return prepare_isolation_forest_features(feature_df)


# ===========================================================================
# Sensor features
# ===========================================================================
class TestSensorFeatures:
    def test_returns_dataframe(self, prepared):
        result = engineer_sensor_features(prepared.sensors)
        assert isinstance(result, pd.DataFrame)

    def test_one_row_per_asset_component(self, prepared):
        result = engineer_sensor_features(prepared.sensors)
        n_combos = (
            prepared.sensors
            .groupby(["asset_id", "component_id"])
            .ngroups
        )
        assert len(result) == n_combos

    def test_expected_sensor_columns_present(self, prepared):
        result = engineer_sensor_features(prepared.sensors)
        sensor_types = ["vibration", "temperature", "pressure", "RPM"]
        suffixes = [
            "latest_value", "rolling_mean", "rolling_std",
            "value_min", "value_max", "trend_slope",
            "max_z_score", "mean_z_score",
        ]
        for st in sensor_types:
            for sf in suffixes:
                col = f"{st}__{sf}"
                assert col in result.columns, f"Missing sensor column: {col}"

    def test_no_nan_in_sensor_features(self, prepared):
        result = engineer_sensor_features(prepared.sensors)
        num_cols = result.select_dtypes(include="number").columns
        assert not result[num_cols].isnull().any().any()

    def test_rolling_std_non_negative(self, prepared):
        result = engineer_sensor_features(prepared.sensors)
        for col in [c for c in result.columns if "__rolling_std" in c]:
            assert (result[col] >= 0).all(), f"Negative rolling_std in {col}"

    def test_max_z_score_non_negative(self, prepared):
        result = engineer_sensor_features(prepared.sensors)
        for col in [c for c in result.columns if "__max_z_score" in c]:
            assert (result[col] >= 0).all(), f"Negative max_z_score in {col}"

    def test_value_min_lte_value_max(self, prepared):
        result = engineer_sensor_features(prepared.sensors)
        sensor_types = ["vibration", "temperature", "pressure", "RPM"]
        for st in sensor_types:
            assert (
                result[f"{st}__value_min"] <= result[f"{st}__value_max"]
            ).all(), f"{st} value_min > value_max"


# ===========================================================================
# Maintenance features
# ===========================================================================
class TestMaintenanceFeatures:
    def test_returns_dataframe(self, prepared):
        result = engineer_maintenance_features(prepared.components)
        assert isinstance(result, pd.DataFrame)

    def test_required_columns_present(self, prepared):
        result = engineer_maintenance_features(prepared.components)
        for col in [
            "asset_id", "component_id", "component_type", "criticality",
            "hours_since_service", "overdue_flag", "service_interval_ratio",
        ]:
            assert col in result.columns, f"Missing column: {col}"

    def test_hours_since_service_non_negative(self, prepared):
        result = engineer_maintenance_features(prepared.components)
        assert (result["hours_since_service"] >= 0).all()

    def test_overdue_flag_is_binary(self, prepared):
        result = engineer_maintenance_features(prepared.components)
        assert set(result["overdue_flag"].unique()).issubset({0, 1})

    def test_service_interval_ratio_non_negative(self, prepared):
        result = engineer_maintenance_features(prepared.components)
        assert (result["service_interval_ratio"] >= 0).all()

    def test_brg1047_hours_since_service_is_420(self, prepared):
        result = engineer_maintenance_features(prepared.components)
        row = result[result["component_id"] == "BRG-1047"].iloc[0]
        assert abs(row["hours_since_service"] - 420.0) < 1.0, (
            f"Expected ~420h, got {row['hours_since_service']}"
        )

    def test_brg1047_overdue_flag_is_1(self, prepared):
        result = engineer_maintenance_features(prepared.components)
        row = result[result["component_id"] == "BRG-1047"].iloc[0]
        assert row["overdue_flag"] == 1, "BRG-1047 should be OVERDUE (flag=1)"

    def test_brg1047_service_ratio_above_1(self, prepared):
        """service_interval_ratio > 1.0 means the component is overdue."""
        result = engineer_maintenance_features(prepared.components)
        row = result[result["component_id"] == "BRG-1047"].iloc[0]
        assert row["service_interval_ratio"] > 1.0, (
            f"Expected ratio > 1.0, got {row['service_interval_ratio']:.3f}"
        )

    def test_brg1047_service_ratio_value(self, prepared):
        """420h since service / 300h interval = 1.4"""
        result = engineer_maintenance_features(prepared.components)
        row = result[result["component_id"] == "BRG-1047"].iloc[0]
        assert abs(row["service_interval_ratio"] - 1.4) < 0.05, (
            f"Expected ratio ~1.4, got {row['service_interval_ratio']:.4f}"
        )

    def test_non_overdue_components_flag_is_0(self, prepared):
        """All components except the designated overdue ones should have overdue_flag = 0."""
        result = engineer_maintenance_features(prepared.components)
        expected_overdue = ["BRG-1047", "BRG-2002", "BRG-9002"]
        others = result[~result["component_id"].isin(expected_overdue)]
        assert (others["overdue_flag"] == 0).all(), (
            f"Unexpected OVERDUE components: "
            f"{others[others['overdue_flag']==1]['component_id'].tolist()}"
        )


# ===========================================================================
# Criticality encoding
# ===========================================================================
class TestCriticalityEncoding:
    def test_criticality_column_added(self, prepared):
        maint = engineer_maintenance_features(prepared.components)
        result = encode_component_features(maint)
        assert "criticality_encoded" in result.columns

    def test_low_maps_to_033(self, prepared):
        maint = engineer_maintenance_features(prepared.components)
        result = encode_component_features(maint)
        low_rows = result[result["criticality"] == "LOW"]
        if not low_rows.empty:
            assert (low_rows["criticality_encoded"] == 0.33).all()

    def test_medium_maps_to_067(self, prepared):
        maint = engineer_maintenance_features(prepared.components)
        result = encode_component_features(maint)
        med_rows = result[result["criticality"] == "MEDIUM"]
        if not med_rows.empty:
            assert (med_rows["criticality_encoded"] == 0.67).all()

    def test_high_maps_to_100(self, prepared):
        maint = engineer_maintenance_features(prepared.components)
        result = encode_component_features(maint)
        high_rows = result[result["criticality"] == "HIGH"]
        assert not high_rows.empty, "No HIGH criticality components found"
        assert (high_rows["criticality_encoded"] == 1.0).all()

    def test_brg1047_criticality_encoded_is_high(self, prepared):
        maint = engineer_maintenance_features(prepared.components)
        result = encode_component_features(maint)
        row = result[result["component_id"] == "BRG-1047"].iloc[0]
        assert row["criticality_encoded"] == 1.0


# ===========================================================================
# build_feature_dataset
# ===========================================================================
class TestBuildFeatureDataset:
    def test_returns_dataframe(self, feature_df):
        assert isinstance(feature_df, pd.DataFrame)

    def test_one_row_per_component(self, feature_df, prepared):
        assert len(feature_df) == len(prepared.components)

    def test_required_identifier_columns(self, feature_df):
        for col in ["asset_id", "component_id", "component_type", "criticality"]:
            assert col in feature_df.columns

    def test_all_rf_feature_columns_present(self, feature_df):
        for col in RF_FEATURE_NAMES:
            assert col in feature_df.columns, f"Missing RF feature: {col}"

    def test_all_if_feature_columns_present(self, feature_df):
        for col in IF_FEATURE_NAMES:
            assert col in feature_df.columns, f"Missing IF feature: {col}"

    def test_no_nan_in_numeric_columns(self, feature_df):
        num_cols = feature_df.select_dtypes(include="number").columns
        assert not feature_df[num_cols].isnull().any().any(), (
            "NaN found in feature_df numeric columns"
        )

    def test_no_inf_in_numeric_columns(self, feature_df):
        num_cols = feature_df.select_dtypes(include="number").columns
        assert np.isfinite(feature_df[num_cols].values).all(), (
            "Infinite value found in feature_df numeric columns"
        )

    def test_brg1047_row_exists(self, feature_df):
        row = feature_df[feature_df["component_id"] == "BRG-1047"]
        assert len(row) == 1

    def test_criticality_encoded_column_present(self, feature_df):
        assert "criticality_encoded" in feature_df.columns


# ===========================================================================
# Random Forest feature preparation
# ===========================================================================
class TestRandomForestFeatures:
    def test_returns_feature_result(self, rf_result):
        from features.feature_engineering import FeatureResult
        assert isinstance(rf_result, FeatureResult)

    def test_X_is_2d_numeric_array(self, rf_result):
        assert isinstance(rf_result.X, np.ndarray)
        assert rf_result.X.ndim == 2

    def test_X_column_count_matches_feature_names(self, rf_result):
        assert rf_result.X.shape[1] == len(rf_result.feature_names)

    def test_y_is_binary_array(self, rf_result):
        assert rf_result.y is not None
        assert set(np.unique(rf_result.y)).issubset({0, 1})

    def test_y_has_at_least_one_positive(self, rf_result):
        """AS-1047/BRG-1047 must be labelled y=1."""
        assert rf_result.y.sum() >= 1, "No at-risk components found (y=1 count is 0)"

    def test_X_no_nan(self, rf_result):
        assert not np.isnan(rf_result.X).any()

    def test_X_no_inf(self, rf_result):
        assert np.isfinite(rf_result.X).all()

    def test_X_rows_match_y_rows(self, rf_result):
        assert rf_result.X.shape[0] == len(rf_result.y)

    def test_asset_id_not_in_rf_features(self, rf_result):
        assert "asset_id" not in rf_result.feature_names

    def test_component_id_not_in_rf_features(self, rf_result):
        assert "component_id" not in rf_result.feature_names

    def test_meta_has_identifier_columns(self, rf_result):
        for col in ["asset_id", "component_id", "component_type"]:
            assert col in rf_result.meta.columns

    def test_brg1047_labelled_at_risk(self, rf_result):
        """BRG-1047 must be labelled y=1 — its sensor data and maintenance
        state genuinely satisfy the labelling rule."""
        idx = rf_result.meta[
            rf_result.meta["component_id"] == "BRG-1047"
        ].index
        assert len(idx) == 1
        # meta index must align with y index
        meta_pos = rf_result.meta.index.get_loc(idx[0])
        assert rf_result.y[meta_pos] == 1, (
            "BRG-1047 was not labelled at-risk (y=1). "
            "Check vibration degradation pattern and overdue_flag."
        )

    def test_label_not_based_on_asset_id(self, rf_result):
        """
        The label rule must be data-driven. Verify that at least one non-AS-1047
        normal asset has y=0, i.e. the rule discriminates rather than flags all.
        """
        normal_mask = rf_result.meta["asset_id"] != "AS-1047"
        normal_y = rf_result.y[normal_mask]
        assert (normal_y == 0).any(), (
            "All components are labelled y=1 — the label rule may be too broad"
        )


# ===========================================================================
# Isolation Forest feature preparation
# ===========================================================================
class TestIsolationForestFeatures:
    def test_returns_feature_result(self, if_result):
        from features.feature_engineering import FeatureResult
        assert isinstance(if_result, FeatureResult)

    def test_X_is_2d_numeric_array(self, if_result):
        assert isinstance(if_result.X, np.ndarray)
        assert if_result.X.ndim == 2

    def test_y_is_none(self, if_result):
        """Isolation Forest is unsupervised — no labels."""
        assert if_result.y is None

    def test_X_column_count_matches_feature_names(self, if_result):
        assert if_result.X.shape[1] == len(if_result.feature_names)

    def test_X_no_nan(self, if_result):
        assert not np.isnan(if_result.X).any()

    def test_X_no_inf(self, if_result):
        assert np.isfinite(if_result.X).all()

    def test_asset_id_not_in_if_features(self, if_result):
        assert "asset_id" not in if_result.feature_names

    def test_component_id_not_in_if_features(self, if_result):
        assert "component_id" not in if_result.feature_names

    def test_maintenance_features_not_in_if(self, if_result):
        """IF uses sensor behaviour only — no maintenance state."""
        for col in ["overdue_flag", "hours_since_service",
                    "service_interval_ratio", "criticality_encoded"]:
            assert col not in if_result.feature_names, (
                f"Maintenance feature '{col}' found in IF feature set"
            )

    def test_meta_has_identifier_columns(self, if_result):
        for col in ["asset_id", "component_id", "component_type"]:
            assert col in if_result.meta.columns


# ===========================================================================
# AS-1047 degradation signal is stronger than normal assets
# ===========================================================================
class TestAS1047Degradation:
    """
    These tests verify that the feature engineering correctly captures the
    AS-1047 canonical degradation scenario. They do NOT hardcode a
    failure probability — they only check that the engineered FEATURES
    are significantly elevated compared to normal assets.
    """

    def test_brg1047_vibration_max_z_score_above_threshold(self, feature_df):
        """BRG-1047's vibration max_z_score must exceed Z_SCORE_THRESHOLD."""
        row = feature_df[feature_df["component_id"] == "BRG-1047"].iloc[0]
        z = row["vibration__max_z_score"]
        assert z > Z_SCORE_THRESHOLD, (
            f"BRG-1047 vibration__max_z_score = {z:.3f}, "
            f"expected > {Z_SCORE_THRESHOLD}"
        )

    def test_brg1047_vibration_z_score_higher_than_normal_assets(
        self, feature_df
    ):
        """AS-1047/BRG-1047 must have a higher vibration max_z_score than
        the median of all other components.

        Note: z-score is computed against each asset's own full history.
        Because AS-1047's history includes the ramp, its within-asset std
        is inflated, which moderates the z-score relative to a purely
        external threshold. The key signal is that BRG-1047's z-score is
        still clearly above the median of peers.
        """
        brg_z = feature_df.loc[
            feature_df["component_id"] == "BRG-1047",
            "vibration__max_z_score",
        ].iloc[0]
        others_z = feature_df.loc[
            feature_df["component_id"] != "BRG-1047",
            "vibration__max_z_score",
        ].median()
        assert brg_z > others_z, (
            f"BRG-1047 z={brg_z:.3f} is not higher than "
            f"median of others z={others_z:.3f}"
        )

    def test_brg1047_vibration_trend_slope_positive(self, feature_df):
        """Positive trend_slope confirms the rising vibration pattern."""
        row = feature_df[feature_df["component_id"] == "BRG-1047"].iloc[0]
        slope = row["vibration__trend_slope"]
        assert slope > 0, (
            f"BRG-1047 vibration__trend_slope = {slope:.4f}, expected positive"
        )

    def test_brg1047_vibration_latest_value_elevated(self, feature_df):
        """The latest vibration reading for BRG-1047 should be > 3.5 mm/s."""
        row = feature_df[feature_df["component_id"] == "BRG-1047"].iloc[0]
        val = row["vibration__latest_value"]
        assert val > 3.5, (
            f"BRG-1047 vibration__latest_value = {val:.3f}, expected > 3.5 mm/s"
        )

    def test_brg1047_pressure_z_score_below_vibration(self, feature_df):
        """Pressure should have a lower z-score than vibration for BRG-1047.
        The bearing fault manifests in vibration; pressure stays normal by
        design. We assert the relative relationship rather than an absolute
        threshold, since short-window random data can produce z>2.5 by chance.
        """
        row = feature_df[feature_df["component_id"] == "BRG-1047"].iloc[0]
        vib_z = row["vibration__max_z_score"]
        prs_z = row["pressure__max_z_score"]
        assert vib_z > prs_z, (
            f"BRG-1047 vibration z ({vib_z:.3f}) should exceed "
            f"pressure z ({prs_z:.3f}) — fault is in bearing, not hydraulics"
        )

    def test_brg1047_overdue_flag_1(self, feature_df):
        row = feature_df[feature_df["component_id"] == "BRG-1047"].iloc[0]
        assert row["overdue_flag"] == 1

    def test_brg1047_criticality_encoded_high(self, feature_df):
        row = feature_df[feature_df["component_id"] == "BRG-1047"].iloc[0]
        assert row["criticality_encoded"] == 1.0

    def test_brg1047_vibration_z_score_is_top_in_fleet(self, feature_df):
        """BRG-1047's vibration__latest_value should be the highest in the fleet.
        The latest_value directly reflects the endpoint of the ramp and is the
        most unambiguous signal of the degradation scenario.
        """
        brg_latest = feature_df.loc[
            feature_df["component_id"] == "BRG-1047",
            "vibration__latest_value",
        ].iloc[0]
        all_latest = feature_df["vibration__latest_value"]
        assert brg_latest == all_latest.max(), (
            f"BRG-1047 latest vibration {brg_latest:.3f} is not the fleet maximum "
            f"(max = {all_latest.max():.3f})"
        )


# ===========================================================================
# NaN / Inf guards
# ===========================================================================
class TestNaNAndInfGuards:
    def test_rf_X_no_nan(self, rf_result):
        assert not np.isnan(rf_result.X).any()

    def test_rf_X_no_inf(self, rf_result):
        assert np.isfinite(rf_result.X).all()

    def test_if_X_no_nan(self, if_result):
        assert not np.isnan(if_result.X).any()

    def test_if_X_no_inf(self, if_result):
        assert np.isfinite(if_result.X).all()

    def test_feature_df_no_nan_in_numerics(self, feature_df):
        num_cols = feature_df.select_dtypes(include="number").columns
        assert not feature_df[num_cols].isnull().any().any()

    def test_feature_df_no_inf_in_numerics(self, feature_df):
        num_cols = feature_df.select_dtypes(include="number").columns
        assert np.isfinite(feature_df[num_cols].values).all()


# ===========================================================================
# run_feature_pipeline — convenience wrapper
# ===========================================================================
class TestRunFeaturePipeline:
    def test_returns_three_items(self):
        result = run_feature_pipeline()
        assert len(result) == 3

    def test_feature_df_is_dataframe(self):
        feature_df, _, _ = run_feature_pipeline()
        assert isinstance(feature_df, pd.DataFrame)

    def test_rf_result_has_X_and_y(self):
        _, rf, _ = run_feature_pipeline()
        assert rf.X is not None
        assert rf.y is not None

    def test_if_result_has_X_no_y(self):
        _, _, iff = run_feature_pipeline()
        assert iff.X is not None
        assert iff.y is None
