"""
AssetSentinel — Synthetic ML Training Data Generator
Member 2 (Selin) | src/backend/member2_ml/training/generate_training_data.py

Purpose:
    Generates a large, balanced synthetic dataset for training the Random
    Forest classifier.  This is SEPARATE from the 21-row demo dataset
    (assets.csv / sensor_data.csv) which is reserved for demo inference.

    Why a separate training set?
        The demo dataset has only 21 component-rows and just ONE positive
        (at-risk) label (BRG-1047). Training a classifier on such a tiny,
        imbalanced set would produce a model that is not generalisable.
        The separate training set provides diverse realistic examples.

    The demo asset AS-1047 / BRG-1047 is NOT part of this training set.
    Its features are engineered from the real demo CSV at inference time
    and passed to the already-trained model via predict_proba().

    Label definition — data-driven, no asset_id rules:
        failure = 1  when  (vibration_max_z > Z_HIGH)
                            AND (overdue_flag == 1)
                            AND (criticality_encoded == 1.0)
        failure = 0  otherwise

    Output:
        src/backend/member2_ml/training/training_data.csv

Architecture position:
    training/generate_training_data.py  ← THIS FILE (Phase 4 support)
    models/train_random_forest.py        (Phase 4 — trains on output of this file)
    prediction/predict.py                (Phase 5 — inference on demo features)
"""

from __future__ import annotations

import os
import random
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Reproducible seed
# ---------------------------------------------------------------------------
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

OUTPUT_DIR  = Path(__file__).resolve().parent          # …/member2_ml/training/
OUTPUT_FILE = OUTPUT_DIR / "training_data.csv"

# ---------------------------------------------------------------------------
# Training dataset size and composition
# ---------------------------------------------------------------------------
N_NORMAL       = 600   # clearly healthy components
N_MODERATE     = 200   # some degradation — borderline
N_HIGH_RISK    = 200   # degraded + overdue + high criticality → failure = 1
N_TOTAL        = N_NORMAL + N_MODERATE + N_HIGH_RISK

# ---------------------------------------------------------------------------
# Label thresholds (must match feature_engineering.py Z_SCORE_THRESHOLD)
# ---------------------------------------------------------------------------
Z_HIGH   = 2.5    # vibration z-score above which anomaly is meaningful
Z_MEDIUM = 1.5    # moderate deviation

# Criticality encoding — must match CRITICALITY_ENCODING in feature_engineering.py
CRIT_LOW  = 0.33
CRIT_MED  = 0.67
CRIT_HIGH = 1.00

# ---------------------------------------------------------------------------
# Feature column names — must exactly match RF_FEATURE_NAMES in
# features/feature_engineering.py so training and inference are aligned.
# ---------------------------------------------------------------------------
SENSOR_TYPES   = ["vibration", "temperature", "pressure", "RPM"]
SENSOR_SUFFIXES_RF = [
    "latest_value", "rolling_mean", "rolling_std",
    "value_min", "value_max", "trend_slope",
    "max_z_score", "mean_z_score",
]
SENSOR_FEATURE_COLS = [
    f"{st}__{sf}" for st in SENSOR_TYPES for sf in SENSOR_SUFFIXES_RF
]
MAINT_FEATURE_COLS = [
    "hours_since_service",
    "overdue_flag",
    "service_interval_ratio",
    "criticality_encoded",
]
ALL_FEATURE_COLS = SENSOR_FEATURE_COLS + MAINT_FEATURE_COLS

# ---------------------------------------------------------------------------
# Realistic sensor operating ranges (mirrors SENSOR_BASELINES in generate_data.py)
# ---------------------------------------------------------------------------
SENSOR_RANGES = {
    # (normal_mean, normal_std, unit_scale_for_degraded)
    "vibration":   (1.5,   0.15,  4.5),   # degraded max ~4.5 mm/s
    "temperature": (75.0,  2.0,   95.0),  # degraded max ~95 °C
    "pressure":    (180.0, 5.0,   180.0), # stays normal
    "RPM":         (2200.0, 50.0, 2200.0),# stays normal
}


# ===========================================================================
# Helper: generate features for one component row
# ===========================================================================

def _make_sensor_row(
    rng: np.random.RandomState,
    sensor_type: str,
    degraded: bool,
    moderate: bool,
) -> dict:
    """
    Simulate summary statistics for one sensor type on one component.

    degraded = True  → mimic AS-1047-style ramping anomaly
    moderate = True  → mild elevation, borderline
    normal           → stays within ±1.5σ baseline
    """
    mean, std, deg_target = SENSOR_RANGES[sensor_type]
    row = {}

    if degraded and sensor_type == "vibration":
        # Strong degradation: the "current" value is near the ramp peak,
        # history contains both normal and degraded readings.
        latest    = rng.uniform(deg_target * 0.85, deg_target * 1.05)
        hist_mean = (mean + latest) / 2           # average of normal + degraded
        hist_std  = abs(latest - mean) / 3.5      # spread of the ramp
        rolling_m = rng.uniform(deg_target * 0.7, latest)
        rolling_s = rng.uniform(0.2, 0.6)
        trend     = rng.uniform(0.05, 0.15)       # clear positive slope
        max_z     = abs(latest - hist_mean) / max(hist_std, 1e-6)
        mean_z    = max_z * rng.uniform(0.4, 0.7) # mean is lower than peak

    elif degraded and sensor_type == "temperature":
        # Mild correlated temperature rise
        latest    = rng.uniform(mean * 1.05, mean * 1.15)
        hist_mean = (mean + latest) / 2
        hist_std  = std * rng.uniform(1.5, 3.0)
        rolling_m = rng.uniform(mean * 1.0, latest)
        rolling_s = std * rng.uniform(0.8, 2.0)
        trend     = rng.uniform(0.02, 0.08)
        max_z     = abs(latest - hist_mean) / max(hist_std, 1e-6)
        mean_z    = max_z * rng.uniform(0.3, 0.6)

    elif moderate and sensor_type == "vibration":
        # Mild elevation — z-score between Z_MEDIUM and Z_HIGH
        latest    = rng.uniform(mean * 1.3, mean * 2.0)
        hist_mean = mean
        hist_std  = std * rng.uniform(2.0, 4.0)
        rolling_m = rng.uniform(mean * 1.1, latest)
        rolling_s = std * rng.uniform(1.5, 3.0)
        trend     = rng.uniform(0.01, 0.05)
        max_z     = rng.uniform(Z_MEDIUM, Z_HIGH)
        mean_z    = max_z * rng.uniform(0.3, 0.6)

    else:
        # Normal readings — z-score well below threshold
        latest    = rng.normal(mean, std)
        hist_mean = mean + rng.uniform(-0.1, 0.1) * mean
        hist_std  = std * rng.uniform(0.8, 1.5)
        rolling_m = rng.normal(hist_mean, std * 0.3)
        rolling_s = std * rng.uniform(0.5, 1.2)
        trend     = rng.normal(0.0, 0.005)
        max_z     = rng.uniform(0.0, Z_MEDIUM)
        mean_z    = max_z * rng.uniform(0.2, 0.6)

    row[f"{sensor_type}__latest_value"] = float(np.clip(latest, mean * 0.3, mean * 4.0))
    row[f"{sensor_type}__rolling_mean"] = float(np.clip(rolling_m, mean * 0.3, mean * 4.0))
    row[f"{sensor_type}__rolling_std"]  = float(max(rolling_s, 0.0))
    row[f"{sensor_type}__value_min"]    = float(np.clip(rolling_m - rolling_s * 2, mean * 0.2, mean * 3.5))
    row[f"{sensor_type}__value_max"]    = float(np.clip(rolling_m + rolling_s * 2, mean * 0.5, mean * 5.0))
    row[f"{sensor_type}__trend_slope"]  = float(trend)
    row[f"{sensor_type}__max_z_score"]  = float(max(max_z, 0.0))
    row[f"{sensor_type}__mean_z_score"] = float(max(mean_z, 0.0))
    return row


def _make_maintenance_features(
    rng: np.random.RandomState,
    degraded: bool,
    moderate: bool,
    criticality: float,
) -> dict:
    """
    Generate maintenance features for one component row.
    """
    if degraded:
        svc_interval     = rng.uniform(200, 400)
        hours_since      = rng.uniform(svc_interval * 1.2, svc_interval * 2.5)
        overdue_flag     = 1
    elif moderate:
        svc_interval     = rng.uniform(200, 500)
        # Overdue only ~40% of the time for moderate cases
        ratio            = rng.uniform(0.7, 1.3)
        hours_since      = svc_interval * ratio
        overdue_flag     = int(hours_since > svc_interval)
    else:
        svc_interval     = rng.uniform(200, 600)
        ratio            = rng.uniform(0.05, 0.85)
        hours_since      = svc_interval * ratio
        overdue_flag     = 0

    svc_ratio = hours_since / max(svc_interval, 1e-6)

    return {
        "hours_since_service":    float(hours_since),
        "overdue_flag":           int(overdue_flag),
        "service_interval_ratio": float(svc_ratio),
        "criticality_encoded":    float(criticality),
    }


# ===========================================================================
# Main generator
# ===========================================================================

def generate_training_data(output_path: Path = OUTPUT_FILE) -> pd.DataFrame:
    """
    Generate the RF training dataset and write it to output_path.

    Returns the DataFrame for immediate use in training.
    """
    rng = np.random.RandomState(RANDOM_SEED)
    rows   : list[dict] = []
    labels : list[int]  = []

    crit_choices     = [CRIT_LOW, CRIT_MED, CRIT_HIGH]
    crit_weights_deg = [0.0, 0.0, 1.0]      # degraded → always HIGH crit
    crit_weights_mod = [0.2, 0.5, 0.3]
    crit_weights_nrm = [0.3, 0.5, 0.2]

    # ---- High-risk examples (failure = 1) ----
    # All three conditions satisfied:  high vib z, overdue, HIGH criticality
    for _ in range(N_HIGH_RISK):
        criticality = CRIT_HIGH
        row = {}
        for st in SENSOR_TYPES:
            row.update(_make_sensor_row(rng, st, degraded=True, moderate=False))
        row.update(_make_maintenance_features(rng, degraded=True, moderate=False,
                                              criticality=criticality))
        # Ensure label rule will fire: clamp vibration z-score above threshold
        row["vibration__max_z_score"] = float(rng.uniform(Z_HIGH + 0.3, Z_HIGH + 3.0))
        rows.append(row)
        labels.append(1)

    # ---- Moderate examples (failure = 0, some stress) ----
    for _ in range(N_MODERATE):
        criticality = float(rng.choice(crit_choices, p=crit_weights_mod))
        row = {}
        for st in SENSOR_TYPES:
            row.update(_make_sensor_row(rng, st, degraded=False, moderate=True))
        row.update(_make_maintenance_features(rng, degraded=False, moderate=True,
                                              criticality=criticality))
        # Moderate rows intentionally BELOW the label threshold (y=0)
        # so the classifier must learn the boundary
        row["vibration__max_z_score"] = float(rng.uniform(0.5, Z_HIGH))
        rows.append(row)
        labels.append(0)

    # ---- Normal examples (failure = 0) ----
    for _ in range(N_NORMAL):
        criticality = float(rng.choice(crit_choices, p=crit_weights_nrm))
        row = {}
        for st in SENSOR_TYPES:
            row.update(_make_sensor_row(rng, st, degraded=False, moderate=False))
        row.update(_make_maintenance_features(rng, degraded=False, moderate=False,
                                              criticality=criticality))
        row["vibration__max_z_score"] = float(rng.uniform(0.0, Z_MEDIUM))
        rows.append(row)
        labels.append(0)

    df = pd.DataFrame(rows, columns=ALL_FEATURE_COLS)
    df["failure_label"] = labels

    # Shuffle so class order is random
    df = df.sample(frac=1.0, random_state=RANDOM_SEED).reset_index(drop=True)

    os.makedirs(output_path.parent, exist_ok=True)
    df.to_csv(output_path, index=False)

    pos = df["failure_label"].sum()
    neg = len(df) - pos
    print(f"[training data] Generated {len(df)} rows — "
          f"positive (failure=1): {pos}, negative (failure=0): {neg}")
    return df


if __name__ == "__main__":
    generate_training_data()
