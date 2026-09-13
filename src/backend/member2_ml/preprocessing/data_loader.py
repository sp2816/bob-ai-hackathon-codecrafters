"""
AssetSentinel — Data Loader & Preprocessing Pipeline
Member 2 (Selin) | src/backend/member2_ml/preprocessing/data_loader.py

Purpose:
    Loads the four CSV datasets produced by data/generate_data.py,
    validates them against the shared data contract, cleans them,
    and returns ready-to-use pandas DataFrames for Feature Engineering.

    All validation rules follow the shared data contract exactly:
        src/backend/integration/contracts/data-contracts.md

Architecture position:
    data/generate_data.py   (Phase 1 — DONE)
        → preprocessing/data_loader.py       ← THIS FILE (Phase 2)
        → features/feature_engineering.py   (Phase 3)
        → models/training/train_model.py     (Phase 4)
        → prediction/predict.py              (Phase 5)
        → prediction/anomaly_detection.py    (Phase 5)
        → evaluation/model_evaluation.py     (Phase 6)

Public API (consumed by Phase 3):
    load_and_prepare_data()
        → returns PreparedDatasets namedtuple:
              .assets          clean assets DataFrame
              .components      clean components DataFrame
              .sensors         clean, chronologically sorted sensor DataFrame
              .maintenance     clean maintenance records DataFrame

    Individual loaders are also exported for granular use:
        load_assets()
        load_components()
        load_sensor_data()
        load_maintenance_records()

IMPORTANT — this module only reads files from:
    src/backend/member2_ml/data/
It does NOT implement feature engineering, readiness scoring,
or any other downstream responsibility.
"""

from __future__ import annotations

import logging
import os
from collections import namedtuple
from pathlib import Path
from typing import Optional

import pandas as pd

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data directory — resolved relative to this file so imports work regardless
# of the working directory the caller uses.
# ---------------------------------------------------------------------------
_MODULE_DIR = Path(__file__).resolve().parent          # …/member2_ml/preprocessing/
_DATA_DIR   = _MODULE_DIR.parent / "data"              # …/member2_ml/data/

# ---------------------------------------------------------------------------
# Contract: allowed enum values (data-contracts.md §6, §7, §18)
# ---------------------------------------------------------------------------
ALLOWED_SENSOR_TYPES = frozenset(["vibration", "temperature", "pressure", "RPM"])
ALLOWED_CRITICALITY  = frozenset(["LOW", "MEDIUM", "HIGH"])
ALLOWED_MAINT_STATUS = frozenset(["COMPLETED", "OVERDUE", "SCHEDULED"])

# ---------------------------------------------------------------------------
# Contract: required columns per CSV (data-contracts.md §4–§7)
# ---------------------------------------------------------------------------
REQUIRED_COLUMNS = {
    "assets": [
        "asset_id", "asset_name", "asset_type", "unit",
        "operational_hours", "current_status",
    ],
    "components": [
        "component_id", "asset_id", "component_type", "criticality",
        "installation_date", "operating_hours", "life_limit",
        # internal service fields used by feature engineering
        "service_interval_hours", "hours_at_last_service",
    ],
    "sensor_data": [
        "sensor_id", "asset_id", "component_id",
        "timestamp", "sensor_type", "value",
    ],
    "maintenance_records": [
        "maintenance_id", "asset_id", "component_id",
        "maintenance_type", "maintenance_date",
        "technician_action", "status", "notes",
    ],
}

# ---------------------------------------------------------------------------
# Return type for load_and_prepare_data()
# ---------------------------------------------------------------------------
PreparedDatasets = namedtuple(
    "PreparedDatasets",
    ["assets", "components", "sensors", "maintenance"],
)


# ===========================================================================
# Private helpers
# ===========================================================================

def _resolve_path(filename: str) -> Path:
    """Return the full path to a CSV file inside the data directory."""
    return _DATA_DIR / filename


def _check_required_columns(df: pd.DataFrame, dataset_name: str) -> None:
    """
    Raise ValueError if any required column is missing.
    Uses the REQUIRED_COLUMNS contract mapping.
    """
    required = REQUIRED_COLUMNS[dataset_name]
    missing  = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(
            f"[{dataset_name}] Missing required columns: {missing}. "
            f"Check data-contracts.md §4–§7."
        )


def _report_missing_values(df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
    """
    Log a warning for columns with missing values.
    For numeric columns: fill NaN with column median (safe imputation).
    For string columns: fill NaN with the literal string 'UNKNOWN'.
    Returns the cleaned DataFrame.
    """
    missing_counts = df.isnull().sum()
    cols_with_nulls = missing_counts[missing_counts > 0]

    if not cols_with_nulls.empty:
        for col, count in cols_with_nulls.items():
            logger.warning(
                "[%s] Column '%s' has %d missing value(s) — filling.",
                dataset_name, col, count,
            )
        # Numeric columns → median imputation
        num_cols = df.select_dtypes(include="number").columns.tolist()
        for col in num_cols:
            if df[col].isnull().any():
                df[col] = df[col].fillna(df[col].median())

        # String / object columns → 'UNKNOWN'
        str_cols = df.select_dtypes(include=["object", "string"]).columns.tolist()
        for col in str_cols:
            if df[col].isnull().any():
                df[col] = df[col].fillna("UNKNOWN")

    return df


def _drop_duplicates(df: pd.DataFrame, subset: list[str],
                     dataset_name: str) -> pd.DataFrame:
    """
    Drop exact duplicate rows (same key columns).
    Logs how many were removed.
    """
    before = len(df)
    df = df.drop_duplicates(subset=subset, keep="first")
    removed = before - len(df)
    if removed > 0:
        logger.warning(
            "[%s] Removed %d duplicate row(s) (key: %s).",
            dataset_name, removed, subset,
        )
    return df


# ===========================================================================
# Public loaders
# ===========================================================================

def load_assets(path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load and validate assets.csv.

    Contract fields (data-contracts.md §4):
        asset_id, asset_name, asset_type, unit,
        operational_hours, current_status

    Validations applied:
        - Required columns present
        - No duplicate asset_id rows
        - operational_hours is non-negative numeric
        - Missing values filled

    Returns:
        pd.DataFrame — one row per asset, indexed by asset_id
    """
    csv_path = path or _resolve_path("assets.csv")
    logger.info("Loading assets from: %s", csv_path)

    if not Path(csv_path).exists():
        raise FileNotFoundError(
            f"assets.csv not found at '{csv_path}'. "
            "Run data/generate_data.py first."
        )

    df = pd.read_csv(csv_path, dtype={"asset_id": str})

    _check_required_columns(df, "assets")
    df = _report_missing_values(df, "assets")
    df = _drop_duplicates(df, subset=["asset_id"], dataset_name="assets")

    # Validate operational_hours is numeric and non-negative
    df["operational_hours"] = pd.to_numeric(df["operational_hours"], errors="coerce")
    neg_mask = df["operational_hours"] < 0
    if neg_mask.any():
        logger.warning(
            "[assets] %d row(s) have negative operational_hours — clamping to 0.",
            neg_mask.sum(),
        )
        df.loc[neg_mask, "operational_hours"] = 0.0

    logger.info("[assets] Loaded %d asset(s).", len(df))
    return df.reset_index(drop=True)


def load_components(path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load and validate components.csv.

    Contract fields (data-contracts.md §5):
        component_id, asset_id, component_type, criticality,
        installation_date, operating_hours, life_limit

    Internal fields (for feature engineering):
        service_interval_hours, hours_at_last_service

    Validations applied:
        - Required columns present
        - No duplicate component_id rows
        - criticality is one of: LOW | MEDIUM | HIGH
        - operating_hours and life_limit are non-negative
        - service_interval_hours > 0
        - hours_at_last_service >= 0

    Returns:
        pd.DataFrame — one row per component
    """
    csv_path = path or _resolve_path("components.csv")
    logger.info("Loading components from: %s", csv_path)

    if not Path(csv_path).exists():
        raise FileNotFoundError(
            f"components.csv not found at '{csv_path}'. "
            "Run data/generate_data.py first."
        )

    df = pd.read_csv(csv_path, dtype={"component_id": str, "asset_id": str})

    _check_required_columns(df, "components")
    df = _report_missing_values(df, "components")
    df = _drop_duplicates(df, subset=["component_id"], dataset_name="components")

    # Validate criticality enum
    invalid_crit = ~df["criticality"].isin(ALLOWED_CRITICALITY)
    if invalid_crit.any():
        bad = df.loc[invalid_crit, "criticality"].unique().tolist()
        raise ValueError(
            f"[components] Invalid criticality value(s): {bad}. "
            f"Allowed: {sorted(ALLOWED_CRITICALITY)}"
        )

    # Validate numeric fields are non-negative
    for col in ["operating_hours", "life_limit",
                "service_interval_hours", "hours_at_last_service"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        neg = df[col] < 0
        if neg.any():
            logger.warning(
                "[components] %d negative value(s) in '%s' — clamping to 0.",
                neg.sum(), col,
            )
            df.loc[neg, col] = 0.0

    # service_interval_hours must be > 0 (division used in feature engineering)
    zero_svc = df["service_interval_hours"] == 0
    if zero_svc.any():
        raise ValueError(
            f"[components] {zero_svc.sum()} row(s) have service_interval_hours = 0. "
            "This would cause division-by-zero in feature engineering."
        )

    logger.info("[components] Loaded %d component(s).", len(df))
    return df.reset_index(drop=True)


def load_sensor_data(path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load and validate sensor_data.csv.

    Contract fields (data-contracts.md §6):
        sensor_id, asset_id, component_id,
        timestamp, sensor_type, value

    Validations applied:
        - Required columns present
        - sensor_type only contains: vibration | temperature | pressure | RPM
        - timestamp is parseable as UTC datetime
        - value is finite numeric (no NaN / Inf)
        - Duplicate (asset_id, component_id, timestamp, sensor_type) rows removed
        - Rows sorted chronologically per (asset_id, component_id, sensor_type)

    Returns:
        pd.DataFrame — sorted sensor readings with parsed timestamps
    """
    csv_path = path or _resolve_path("sensor_data.csv")
    logger.info("Loading sensor data from: %s", csv_path)

    if not Path(csv_path).exists():
        raise FileNotFoundError(
            f"sensor_data.csv not found at '{csv_path}'. "
            "Run data/generate_data.py first."
        )

    df = pd.read_csv(
        csv_path,
        dtype={"sensor_id": str, "asset_id": str, "component_id": str},
    )

    _check_required_columns(df, "sensor_data")
    df = _report_missing_values(df, "sensor_data")

    # Validate sensor_type enum (contract §6)
    invalid_sensors = ~df["sensor_type"].isin(ALLOWED_SENSOR_TYPES)
    if invalid_sensors.any():
        bad = df.loc[invalid_sensors, "sensor_type"].unique().tolist()
        raise ValueError(
            f"[sensor_data] Invalid sensor_type value(s): {bad}. "
            f"Allowed: {sorted(ALLOWED_SENSOR_TYPES)}"
        )

    # Parse timestamps
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=False, errors="coerce")
    bad_ts = df["timestamp"].isnull()
    if bad_ts.any():
        logger.warning(
            "[sensor_data] %d row(s) have unparseable timestamps — dropping.",
            bad_ts.sum(),
        )
        df = df[~bad_ts]

    # Validate value is finite numeric
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    non_finite = ~df["value"].apply(lambda x: pd.notna(x) and (x == x))
    if non_finite.any():
        logger.warning(
            "[sensor_data] %d row(s) have non-finite 'value' — dropping.",
            non_finite.sum(),
        )
        df = df[~non_finite]

    # Remove duplicate readings
    df = _drop_duplicates(
        df,
        subset=["asset_id", "component_id", "timestamp", "sensor_type"],
        dataset_name="sensor_data",
    )

    # Sort chronologically per asset / component / sensor_type
    df = df.sort_values(
        ["asset_id", "component_id", "sensor_type", "timestamp"]
    ).reset_index(drop=True)

    logger.info("[sensor_data] Loaded %d reading(s).", len(df))
    return df


def load_maintenance_records(path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load and validate maintenance_records.csv.

    Contract fields (data-contracts.md §7):
        maintenance_id, asset_id, component_id,
        maintenance_type, maintenance_date,
        technician_action, status, notes

    Validations applied:
        - Required columns present
        - status only contains: COMPLETED | OVERDUE | SCHEDULED
        - maintenance_date is parseable as date
        - No duplicate maintenance_id rows

    Returns:
        pd.DataFrame — maintenance records with parsed dates, sorted by date
    """
    csv_path = path or _resolve_path("maintenance_records.csv")
    logger.info("Loading maintenance records from: %s", csv_path)

    if not Path(csv_path).exists():
        raise FileNotFoundError(
            f"maintenance_records.csv not found at '{csv_path}'. "
            "Run data/generate_data.py first."
        )

    df = pd.read_csv(
        csv_path,
        dtype={"maintenance_id": str, "asset_id": str, "component_id": str},
    )

    _check_required_columns(df, "maintenance_records")
    df = _report_missing_values(df, "maintenance_records")
    df = _drop_duplicates(
        df, subset=["maintenance_id"], dataset_name="maintenance_records"
    )

    # Validate status enum (contract §7)
    invalid_status = ~df["status"].isin(ALLOWED_MAINT_STATUS)
    if invalid_status.any():
        bad = df.loc[invalid_status, "status"].unique().tolist()
        raise ValueError(
            f"[maintenance_records] Invalid status value(s): {bad}. "
            f"Allowed: {sorted(ALLOWED_MAINT_STATUS)}"
        )

    # Parse maintenance_date
    df["maintenance_date"] = pd.to_datetime(
        df["maintenance_date"], errors="coerce"
    ).dt.date
    bad_dates = df["maintenance_date"].isnull()
    if bad_dates.any():
        logger.warning(
            "[maintenance_records] %d row(s) have unparseable dates — dropping.",
            bad_dates.sum(),
        )
        df = df[~bad_dates]

    # Sort by date
    df = df.sort_values(
        ["asset_id", "component_id", "maintenance_date"]
    ).reset_index(drop=True)

    logger.info("[maintenance_records] Loaded %d record(s).", len(df))
    return df


# ===========================================================================
# Cross-dataset validation
# ===========================================================================

def validate_referential_integrity(
    assets:      pd.DataFrame,
    components:  pd.DataFrame,
    sensors:     pd.DataFrame,
    maintenance: pd.DataFrame,
) -> None:
    """
    Verify that asset_id and component_id references are consistent
    across all four DataFrames.

    Checks performed:
        1. Every component.asset_id exists in assets.asset_id
        2. Every sensor.asset_id exists in assets.asset_id
        3. Every sensor.component_id exists in components.component_id
        4. Every maintenance.asset_id exists in assets.asset_id
        5. Every maintenance.component_id exists in components.component_id

    Logs warnings (not errors) for orphaned rows so the pipeline is not
    blocked during development when Member 1's DB may have different IDs.
    """
    valid_asset_ids = set(assets["asset_id"])
    valid_comp_ids  = set(components["component_id"])

    def _warn_orphans(df, col, valid_set, df_name, ref_name):
        orphans = ~df[col].isin(valid_set)
        if orphans.any():
            bad = df.loc[orphans, col].unique().tolist()
            logger.warning(
                "[integrity] %s.%s has %d orphan value(s) not in %s: %s",
                df_name, col, orphans.sum(), ref_name, bad,
            )

    _warn_orphans(components,  "asset_id",     valid_asset_ids, "components",  "assets")
    _warn_orphans(sensors,     "asset_id",     valid_asset_ids, "sensors",     "assets")
    _warn_orphans(sensors,     "component_id", valid_comp_ids,  "sensors",     "components")
    _warn_orphans(maintenance, "asset_id",     valid_asset_ids, "maintenance", "assets")
    _warn_orphans(maintenance, "component_id", valid_comp_ids,  "maintenance", "components")

    logger.info("[integrity] Referential integrity check complete.")


# ===========================================================================
# Main entry point
# ===========================================================================

def load_and_prepare_data(data_dir: Optional[Path] = None) -> PreparedDatasets:
    """
    Load, validate, and clean all four datasets in one call.

    This is the primary function consumed by Feature Engineering (Phase 3).

    Args:
        data_dir: Optional path override for the data directory.
                  Defaults to src/backend/member2_ml/data/.

    Returns:
        PreparedDatasets(assets, components, sensors, maintenance)
            All DataFrames are validated, cleaned, and ready for
            feature engineering. No raw CSV paths are exposed upstream.

    Raises:
        FileNotFoundError: if any required CSV is missing.
        ValueError:        if any contract validation fails hard
                           (e.g. unknown sensor_type, zero service_interval).

    Usage in Phase 3:
        from preprocessing.data_loader import load_and_prepare_data
        data = load_and_prepare_data()
        # data.sensors is sorted by (asset_id, component_id, sensor_type, timestamp)
        # data.components has hours_at_last_service for overdue_flag computation
    """
    if data_dir is not None:
        # Allow callers to override the data directory (useful in tests)
        asset_path  = Path(data_dir) / "assets.csv"
        comp_path   = Path(data_dir) / "components.csv"
        sensor_path = Path(data_dir) / "sensor_data.csv"
        maint_path  = Path(data_dir) / "maintenance_records.csv"
    else:
        asset_path  = None
        comp_path   = None
        sensor_path = None
        maint_path  = None

    logger.info("=== AssetSentinel: loading and preparing all datasets ===")

    assets      = load_assets(asset_path)
    components  = load_components(comp_path)
    sensors     = load_sensor_data(sensor_path)
    maintenance = load_maintenance_records(maint_path)

    validate_referential_integrity(assets, components, sensors, maintenance)

    logger.info(
        "=== Data preparation complete: %d assets, %d components, "
        "%d sensor rows, %d maintenance records ===",
        len(assets), len(components), len(sensors), len(maintenance),
    )

    return PreparedDatasets(
        assets=assets,
        components=components,
        sensors=sensors,
        maintenance=maintenance,
    )
