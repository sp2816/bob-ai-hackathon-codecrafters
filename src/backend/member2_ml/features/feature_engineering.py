"""
AssetSentinel — Feature Engineering Pipeline
Member 2 (Selin) | src/backend/member2_ml/features/feature_engineering.py

Purpose:
    Transforms the clean DataFrames produced by preprocessing/data_loader.py
    into ML-ready numeric feature sets for:
        1. Random Forest   — failure probability classification
        2. Isolation Forest — anomaly detection

    All features are derived from actual sensor readings and maintenance
    records. No labels or anomaly scores are manually assigned here.
    AS-1047's HIGH-risk status must emerge from model inference, not
    from rules based on asset_id.

Architecture position:
    data/generate_data.py            (Phase 1 — DONE)
    preprocessing/data_loader.py     (Phase 2 — DONE)
        → features/feature_engineering.py   ← THIS FILE (Phase 3)
        → models/training/train_model.py     (Phase 4)
        → prediction/predict.py              (Phase 5)
        → prediction/anomaly_detection.py    (Phase 5)
        → evaluation/model_evaluation.py     (Phase 6)

Public API (consumed by Phase 4 training and Phase 5 inference):

    build_feature_dataset(data) → pd.DataFrame
        One row per (asset_id, component_id). Contains identifier columns
        plus all engineered numeric features.

    prepare_random_forest_features(feature_df)
        → FeatureResult(X, y, feature_names, meta)
        X:    numeric feature matrix for RF training/inference
        y:    synthetic binary training label (0=normal, 1=at-risk)
        meta: identifier columns (asset_id, component_id, component_type)

    prepare_isolation_forest_features(feature_df)
        → FeatureResult(X, y=None, feature_names, meta)
        X:    sensor-behaviour features only (no maintenance, no criticality)
        y:    None — IF is unsupervised

IMPORTANT — this module does NOT:
    - Train any model
    - Assign manual anomaly scores
    - Use asset_id as a decision rule
    - Implement readiness scoring (Member 3's responsibility)
"""

from __future__ import annotations

import logging
from collections import namedtuple
from typing import Optional

import numpy as np
import pandas as pd

from preprocessing.data_loader import PreparedDatasets, load_and_prepare_data

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rolling window size — must match dataset density.
# With 200 readings per sensor, a window of 20 covers ~10% of the history
# and is large enough to capture trend while remaining responsive.
# ---------------------------------------------------------------------------
ROLLING_WINDOW = 20

# ---------------------------------------------------------------------------
# Criticality encoding — LOW=0.33, MEDIUM=0.67, HIGH=1.0
# These match the normalised scale used in the readiness score formula
# (data-contracts.md §15) so the Readiness Engine and ML layer share
# the same numeric representation of criticality.
# ---------------------------------------------------------------------------
CRITICALITY_ENCODING = {
    "LOW":    0.33,
    "MEDIUM": 0.67,
    "HIGH":   1.00,
}

# ---------------------------------------------------------------------------
# Synthetic label thresholds (Random Forest training only)
# A component is labelled at-risk (y=1) when ALL three conditions hold:
#   1. max_z_score   > Z_SCORE_THRESHOLD     — sensor is behaving anomalously
#   2. overdue_flag  == 1                    — inspection is overdue
#   3. criticality   == HIGH (encoded 1.0)   — component matters for readiness
#
# Crucially this does NOT reference asset_id — the label comes from
# the measured features, so AS-1047 earns y=1 because its sensor data
# and maintenance record genuinely satisfy these conditions.
# ---------------------------------------------------------------------------
Z_SCORE_THRESHOLD = 2.5    # readings above 2.5σ from asset's own baseline

# ---------------------------------------------------------------------------
# Return type shared by both prepare_*_features functions
# ---------------------------------------------------------------------------
FeatureResult = namedtuple(
    "FeatureResult",
    ["X", "y", "feature_names", "meta"],
)


# ===========================================================================
# 1. Sensor features
# ===========================================================================

def engineer_sensor_features(sensors: pd.DataFrame) -> pd.DataFrame:
    """
    Derive per-(asset_id, component_id) aggregated sensor features from
    the chronologically sorted sensor_data DataFrame.

    Why these features?
    ───────────────────
    latest_value          The most recent reading; used as the current state.
    rolling_mean          Short-term average; smooths noise to reveal trends.
    rolling_std           Short-term variability; high std suggests instability.
    value_min / value_max Range over the full history; flags sustained outliers.
    trend_slope           Linear regression slope over the last ROLLING_WINDOW
                          readings. Positive and steep → degradation in progress.
    max_z_score           Peak deviation from the asset's own mean, normalised
                          by its own std. Detects anomalies relative to
                          each asset's individual baseline (not a fleet-wide
                          threshold), which is the correct approach for
                          Isolation Forest.
    mean_z_score          Average deviation — distinguishes a sustained trend
                          from a single spike.

    Input:
        sensors — clean sensor DataFrame from load_sensor_data()
                  sorted by (asset_id, component_id, sensor_type, timestamp)

    Returns:
        pd.DataFrame with columns:
            asset_id, component_id,
            {sensor_type}__latest_value,
            {sensor_type}__rolling_mean,
            {sensor_type}__rolling_std,
            {sensor_type}__value_min,
            {sensor_type}__value_max,
            {sensor_type}__trend_slope,
            {sensor_type}__max_z_score,
            {sensor_type}__mean_z_score
    """
    records = []

    groups = sensors.groupby(["asset_id", "component_id", "sensor_type"])

    for (asset_id, component_id, sensor_type), grp in groups:
        grp = grp.sort_values("timestamp")
        vals = grp["value"].values.astype(float)
        n    = len(vals)

        # --- latest value ---
        latest_value = float(vals[-1])

        # --- rolling stats (use last ROLLING_WINDOW readings) ---
        window = vals[-ROLLING_WINDOW:] if n >= ROLLING_WINDOW else vals
        rolling_mean = float(np.mean(window))
        rolling_std  = float(np.std(window)) if len(window) > 1 else 0.0

        # --- full-history range ---
        value_min = float(np.min(vals))
        value_max = float(np.max(vals))

        # --- trend slope (linear fit over last ROLLING_WINDOW readings) ---
        if len(window) >= 2:
            x          = np.arange(len(window), dtype=float)
            slope, _   = np.polyfit(x, window, 1)
            trend_slope = float(slope)
        else:
            trend_slope = 0.0

        # --- z-score against the asset's own full-history baseline ---
        global_mean = float(np.mean(vals))
        global_std  = float(np.std(vals))

        if global_std > 1e-9:
            z_scores   = (vals - global_mean) / global_std
            max_z_score  = float(np.max(np.abs(z_scores)))
            mean_z_score = float(np.mean(np.abs(z_scores)))
        else:
            # Constant signal — z-scores are all 0
            max_z_score  = 0.0
            mean_z_score = 0.0

        records.append({
            "asset_id":                             asset_id,
            "component_id":                         component_id,
            f"{sensor_type}__latest_value":         latest_value,
            f"{sensor_type}__rolling_mean":         rolling_mean,
            f"{sensor_type}__rolling_std":          rolling_std,
            f"{sensor_type}__value_min":            value_min,
            f"{sensor_type}__value_max":            value_max,
            f"{sensor_type}__trend_slope":          trend_slope,
            f"{sensor_type}__max_z_score":          max_z_score,
            f"{sensor_type}__mean_z_score":         mean_z_score,
        })

    # Pivot: one row per (asset_id, component_id) with all sensor columns
    df = pd.DataFrame(records)
    # Merge sensor-type sub-rows into a single row per (asset, component)
    df = (
        df
        .groupby(["asset_id", "component_id"], sort=False)
        .first()              # all feature columns are already unique per sensor_type
        .reset_index()
    )

    # Because groupby/first collapses different sensor_type records that share
    # the same (asset, component) key, we need to pivot properly instead.
    # Re-do the pivot explicitly for correctness.
    df_pivot = _pivot_sensor_records(records)

    logger.info(
        "[features] Sensor features: %d rows, %d columns",
        len(df_pivot), len(df_pivot.columns),
    )
    return df_pivot


def _pivot_sensor_records(records: list[dict]) -> pd.DataFrame:
    """
    Merge the per-(asset, component, sensor_type) records so each
    (asset_id, component_id) pair occupies exactly one row.
    """
    # Build a dict keyed by (asset_id, component_id)
    merged: dict[tuple, dict] = {}
    for rec in records:
        key = (rec["asset_id"], rec["component_id"])
        if key not in merged:
            merged[key] = {"asset_id": rec["asset_id"],
                           "component_id": rec["component_id"]}
        # Copy all sensor_type__ columns
        for k, v in rec.items():
            if k not in ("asset_id", "component_id"):
                merged[key][k] = v

    return pd.DataFrame(list(merged.values()))


# ===========================================================================
# 2. Maintenance features
# ===========================================================================

def engineer_maintenance_features(components: pd.DataFrame) -> pd.DataFrame:
    """
    Derive maintenance-related numeric features from the components DataFrame.

    Features produced per component:
    ─────────────────────────────────
    hours_since_service
        = operating_hours − hours_at_last_service
        Measures how long it has been since the last inspection.
        Higher values suggest the component is moving toward or past its
        inspection interval. Used directly by Random Forest.

    overdue_flag  (0 or 1)
        = 1 if hours_since_service > service_interval_hours
        Binary flag for the hard-rule trigger: an overdue inspection on a
        HIGH criticality component immediately causes NOT_READY status in
        Member 3's Readiness Engine. Also a key RF training label condition.

    service_interval_ratio
        = hours_since_service / service_interval_hours
        Continuous version of overdue_flag. Values > 1.0 mean overdue.
        Smoothly captures "how overdue" rather than a hard binary.
        Division-by-zero protected (service_interval_hours > 0 guaranteed
        by data_loader validation).

    Input:
        components — clean components DataFrame from load_components()

    Returns:
        pd.DataFrame with columns:
            asset_id, component_id, component_type, criticality,
            hours_since_service, overdue_flag, service_interval_ratio
    """
    df = components.copy()

    df["hours_since_service"] = (
        df["operating_hours"] - df["hours_at_last_service"]
    ).clip(lower=0.0)  # safety clamp — should never be negative given valid data

    df["overdue_flag"] = (
        df["hours_since_service"] > df["service_interval_hours"]
    ).astype(int)

    # service_interval_hours > 0 is guaranteed by data_loader
    df["service_interval_ratio"] = (
        df["hours_since_service"] / df["service_interval_hours"]
    )

    result = df[[
        "asset_id", "component_id", "component_type", "criticality",
        "hours_since_service", "overdue_flag", "service_interval_ratio",
    ]].copy()

    logger.info(
        "[features] Maintenance features: %d rows. Overdue: %d",
        len(result), result["overdue_flag"].sum(),
    )
    return result.reset_index(drop=True)


# ===========================================================================
# 3. Component criticality encoding
# ===========================================================================

def encode_component_features(maintenance_features: pd.DataFrame) -> pd.DataFrame:
    """
    Encode the categorical criticality field into a numeric value.

    Encoding (matches data-contracts.md §15 readiness score weights):
        LOW    → 0.33
        MEDIUM → 0.67
        HIGH   → 1.00

    Using this scale means the RF model and the Readiness Engine's
    component_criticality weight share the same numeric representation,
    which keeps the two systems interpretable together.

    Input:
        maintenance_features — output of engineer_maintenance_features()

    Returns:
        Same DataFrame with an additional column:
            criticality_encoded  (float 0.33 / 0.67 / 1.00)
    """
    df = maintenance_features.copy()
    df["criticality_encoded"] = (
        df["criticality"].map(CRITICALITY_ENCODING).fillna(0.67)
    )
    unknown = df["criticality_encoded"].isna()
    if unknown.any():
        logger.warning(
            "[features] %d component(s) had unknown criticality — defaulted to 0.67.",
            unknown.sum(),
        )
    logger.info("[features] Criticality encoding applied.")
    return df


# ===========================================================================
# 4. Build the combined feature dataset
# ===========================================================================

def build_feature_dataset(data: PreparedDatasets) -> pd.DataFrame:
    """
    Orchestrate all three feature-engineering steps and merge the results
    into one ML-ready feature DataFrame.

    Rows:    one per (asset_id, component_id)
    Columns: asset_id, component_id, component_type, criticality,
             criticality_encoded,
             hours_since_service, overdue_flag, service_interval_ratio,
             vibration__*, temperature__*, pressure__*, RPM__*

    Identifier columns (asset_id, component_id, component_type, criticality)
    are kept in the DataFrame for traceability but are NOT passed to the
    model as input features — see prepare_random_forest_features() and
    prepare_isolation_forest_features().

    Args:
        data — PreparedDatasets namedtuple from load_and_prepare_data()

    Returns:
        pd.DataFrame — one row per component, all features numeric,
        no NaN, no infinite values.
    """
    # Step 1 — sensor features
    sensor_feats = engineer_sensor_features(data.sensors)

    # Step 2 — maintenance features
    maint_feats = engineer_maintenance_features(data.components)

    # Step 3 — criticality encoding
    maint_feats = encode_component_features(maint_feats)

    # Step 4 — merge on (asset_id, component_id)
    feature_df = pd.merge(
        maint_feats,
        sensor_feats,
        on=["asset_id", "component_id"],
        how="left",
    )

    # Step 5 — fill any NaN from missing sensor coverage with 0
    numeric_cols = feature_df.select_dtypes(include="number").columns
    nan_count = feature_df[numeric_cols].isnull().sum().sum()
    if nan_count > 0:
        logger.warning(
            "[features] Filling %d NaN value(s) in numeric columns with 0.",
            nan_count,
        )
        feature_df[numeric_cols] = feature_df[numeric_cols].fillna(0.0)

    # Step 6 — replace infinite values with 0
    feature_df[numeric_cols] = feature_df[numeric_cols].replace(
        [np.inf, -np.inf], 0.0
    )

    logger.info(
        "[features] Feature dataset built: %d rows x %d columns.",
        len(feature_df), len(feature_df.columns),
    )
    return feature_df.reset_index(drop=True)


# ===========================================================================
# 5. Random Forest feature preparation
# ===========================================================================

# Features used as input to the Random Forest classifier.
# These cover both sensor behaviour and maintenance state.
# Sensor types are expanded with the __ prefix convention below.
_RF_SENSOR_TYPES = ["vibration", "temperature", "pressure", "RPM"]
_RF_SENSOR_SUFFIXES = [
    "latest_value", "rolling_mean", "rolling_std",
    "value_min", "value_max", "trend_slope",
    "max_z_score", "mean_z_score",
]
_RF_MAINTENANCE_FEATURES = [
    "hours_since_service",
    "overdue_flag",
    "service_interval_ratio",
    "criticality_encoded",
]

RF_FEATURE_NAMES: list[str] = (
    [f"{st}__{sf}" for st in _RF_SENSOR_TYPES for sf in _RF_SENSOR_SUFFIXES]
    + _RF_MAINTENANCE_FEATURES
)


def prepare_random_forest_features(feature_df: pd.DataFrame) -> FeatureResult:
    """
    Extract the Random Forest input matrix X and synthetic training label y.

    X:  Numeric feature matrix — shape (n_components, n_features).
        Contains sensor summary statistics + maintenance state.
        Does NOT contain asset_id, component_id, or component_type.

    y:  Synthetic binary training label — shape (n_components,).
        y = 1 (at-risk) when ALL three conditions hold:
            max_z_score for vibration  >  Z_SCORE_THRESHOLD (2.5)
            overdue_flag               == 1
            criticality_encoded        == 1.0 (HIGH)

        This labelling rule is purely data-driven:
            - It uses features derived from sensor readings and maintenance hours
            - It does NOT reference asset_id
            - AS-1047 earns y=1 because its data genuinely satisfies the rule

    meta: DataFrame with (asset_id, component_id, component_type) for
          tracing predictions back to assets after inference.

    Args:
        feature_df — output of build_feature_dataset()

    Returns:
        FeatureResult(X, y, feature_names, meta)
    """
    # Verify all required feature columns exist
    available_cols = set(feature_df.columns)
    missing = [c for c in RF_FEATURE_NAMES if c not in available_cols]
    if missing:
        raise ValueError(
            f"[RF features] Missing columns in feature_df: {missing}. "
            "Ensure build_feature_dataset() was called with complete sensor data."
        )

    X = feature_df[RF_FEATURE_NAMES].values.astype(float)

    # Synthetic training label — derived from features, not from asset_id
    vib_max_z      = feature_df["vibration__max_z_score"].values
    overdue        = feature_df["overdue_flag"].values
    crit_encoded   = feature_df["criticality_encoded"].values

    y = (
        (vib_max_z    >  Z_SCORE_THRESHOLD) &
        (overdue      == 1) &
        (crit_encoded == 1.0)
    ).astype(int)

    meta = feature_df[["asset_id", "component_id", "component_type"]].copy()

    logger.info(
        "[RF features] X shape: %s | y=1 (at-risk): %d / %d",
        X.shape, int(y.sum()), len(y),
    )

    return FeatureResult(
        X=X,
        y=y,
        feature_names=RF_FEATURE_NAMES,
        meta=meta,
    )


# ===========================================================================
# 6. Isolation Forest feature preparation
# ===========================================================================

# Features used as input to the Isolation Forest.
# Isolation Forest is unsupervised — it detects anomalies relative to
# the distribution of the training data.
# We use ONLY sensor-behaviour features here:
#   - No maintenance state (that would conflate two different failure modes)
#   - No criticality (structural info, not sensor behaviour)
#   - No asset_id / component_id (would create spurious groupings)
# The IF learns what "normal" sensor behaviour looks like across all
# assets and flags deviations as anomalies.
_IF_SENSOR_SUFFIXES = [
    "latest_value", "rolling_mean", "rolling_std",
    "value_max", "trend_slope", "max_z_score",
]

IF_FEATURE_NAMES: list[str] = [
    f"{st}__{sf}"
    for st in _RF_SENSOR_TYPES
    for sf in _IF_SENSOR_SUFFIXES
]


def prepare_isolation_forest_features(feature_df: pd.DataFrame) -> FeatureResult:
    """
    Extract the Isolation Forest input matrix X.

    X:  Sensor-behaviour features only — shape (n_components, n_if_features).
        No maintenance state, no criticality, no identifiers.

    y:  None — Isolation Forest is unsupervised; labels are not used.

    meta: DataFrame with (asset_id, component_id, component_type) for
          tracing anomaly scores back to assets after inference.

    Args:
        feature_df — output of build_feature_dataset()

    Returns:
        FeatureResult(X, y=None, feature_names, meta)
    """
    available_cols = set(feature_df.columns)
    missing = [c for c in IF_FEATURE_NAMES if c not in available_cols]
    if missing:
        raise ValueError(
            f"[IF features] Missing columns in feature_df: {missing}. "
            "Ensure build_feature_dataset() was called with complete sensor data."
        )

    X = feature_df[IF_FEATURE_NAMES].values.astype(float)
    meta = feature_df[["asset_id", "component_id", "component_type"]].copy()

    logger.info(
        "[IF features] X shape: %s (unsupervised — no y)",
        X.shape,
    )

    return FeatureResult(
        X=X,
        y=None,
        feature_names=IF_FEATURE_NAMES,
        meta=meta,
    )


# ===========================================================================
# Convenience: run the full pipeline in one call
# ===========================================================================

def run_feature_pipeline(
    data: Optional[PreparedDatasets] = None,
) -> tuple[pd.DataFrame, FeatureResult, FeatureResult]:
    """
    Convenience wrapper that runs the complete Phase 3 pipeline:
        load data (if not provided) → build features → prepare RF & IF inputs

    Returns:
        (feature_df, rf_result, if_result)

    Typical usage in train_model.py (Phase 4):
        from features.feature_engineering import run_feature_pipeline
        feature_df, rf_result, if_result = run_feature_pipeline()
        # rf_result.X, rf_result.y  → train Random Forest
        # if_result.X               → train Isolation Forest
    """
    if data is None:
        data = load_and_prepare_data()
    feature_df = build_feature_dataset(data)
    rf_result  = prepare_random_forest_features(feature_df)
    if_result  = prepare_isolation_forest_features(feature_df)
    return feature_df, rf_result, if_result
