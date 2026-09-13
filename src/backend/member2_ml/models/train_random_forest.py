"""
AssetSentinel — Random Forest Training Script
Member 2 (Selin) | src/backend/member2_ml/models/train_random_forest.py

Purpose:
    1. Generates (or loads) the synthetic RF training dataset.
    2. Trains a RandomForestClassifier.
    3. Evaluates on a held-out test split.
    4. Saves the trained model and feature column order as artifacts.
    5. Validates AS-1047's real-world inference probability using the
       ACTUAL demo feature engineering pipeline — no hardcoding.

Run:
    python src/backend/member2_ml/models/train_random_forest.py

Architecture position:
    training/generate_training_data.py  (Phase 4 support)
        → models/train_random_forest.py     ← THIS FILE (Phase 4)
        → prediction/predict.py              (Phase 5 — loads saved artifact)

Artifacts produced:
    models/artifacts/random_forest_model.joblib
    models/artifacts/feature_columns.json

IMPORTANT — AGENTS.md locked rules obeyed here:
    - AS-1047 failure_probability comes from predict_proba() on real features
    - No hardcoding of probabilities per asset_id
    - No RUL output
    - No readiness scoring (that is Member 3's responsibility)
"""

from __future__ import annotations

import json
import sys
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split

# ---------------------------------------------------------------------------
# Ensure member2_ml root is on sys.path for relative imports
# ---------------------------------------------------------------------------
_ML_ROOT = Path(__file__).resolve().parent.parent   # …/member2_ml/
if str(_ML_ROOT) not in sys.path:
    sys.path.insert(0, str(_ML_ROOT))

from features.feature_engineering import (
    RF_FEATURE_NAMES,
    build_feature_dataset,
    prepare_random_forest_features,
)
from models.model_utils import (
    RF_MODEL_PATH,
    save_artifact,
    save_feature_columns,
)
from preprocessing.data_loader import load_and_prepare_data
from training.generate_training_data import (
    ALL_FEATURE_COLS,
    OUTPUT_FILE as TRAINING_DATA_FILE,
    generate_training_data,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Hyperparameters — documented for reproducibility
# ---------------------------------------------------------------------------
RF_CONFIG = {
    "n_estimators":    200,
    "max_depth":       8,
    "min_samples_leaf": 2,
    "class_weight":   "balanced",   # handles any residual imbalance
    "random_state":   42,
    "n_jobs":         -1,
}
TEST_SIZE    = 0.20   # 80/20 split
RANDOM_STATE = 42


# ===========================================================================
# Step 1 — Load / generate training data
# ===========================================================================

def load_or_generate_training_data() -> pd.DataFrame:
    """Load training_data.csv if it exists, otherwise generate it."""
    if TRAINING_DATA_FILE.exists():
        df = pd.read_csv(TRAINING_DATA_FILE)
        logger.info("Loaded existing training data: %d rows", len(df))
    else:
        logger.info("Generating training data …")
        df = generate_training_data()
    return df


# ===========================================================================
# Step 2 — Prepare X, y
# ===========================================================================

def prepare_training_arrays(
    df: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """
    Extract the numeric feature matrix X and label vector y from the
    training DataFrame.

    Returns:
        X              — shape (n_samples, n_features)
        y              — shape (n_samples,) — binary 0/1
        feature_cols   — ordered list of column names (MUST match RF_FEATURE_NAMES)
    """
    # Verify all required columns are present
    missing = [c for c in RF_FEATURE_NAMES if c not in df.columns]
    if missing:
        raise ValueError(
            f"Training data is missing required feature columns: {missing}"
        )

    feature_cols = RF_FEATURE_NAMES          # canonical order from feature_engineering.py
    X = df[feature_cols].values.astype(float)
    y = df["failure_label"].values.astype(int)

    assert not np.isnan(X).any(),  "NaN in training X"
    assert np.isfinite(X).all(),   "Inf in training X"

    return X, y, feature_cols


# ===========================================================================
# Step 3 — Train
# ===========================================================================

def train_random_forest(
    X_train: np.ndarray,
    y_train: np.ndarray,
) -> RandomForestClassifier:
    """
    Train a RandomForestClassifier on the supplied training data.
    Uses RF_CONFIG for all hyperparameters.
    """
    clf = RandomForestClassifier(**RF_CONFIG)
    clf.fit(X_train, y_train)
    logger.info(
        "Random Forest trained — %d estimators, max_depth=%s",
        RF_CONFIG["n_estimators"], RF_CONFIG["max_depth"],
    )
    return clf


# ===========================================================================
# Step 4 — Evaluate
# ===========================================================================

def evaluate_model(
    clf: RandomForestClassifier,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
) -> dict:
    """
    Compute and print training + test metrics.
    Returns a dict of test metrics for programmatic access.
    """
    y_train_pred = clf.predict(X_train)
    y_test_pred  = clf.predict(X_test)

    train_acc = accuracy_score(y_train, y_train_pred)
    test_acc  = accuracy_score(y_test,  y_test_pred)
    test_prec = precision_score(y_test, y_test_pred, zero_division=0)
    test_rec  = recall_score(y_test,    y_test_pred, zero_division=0)
    test_f1   = f1_score(y_test,        y_test_pred, zero_division=0)
    cm        = confusion_matrix(y_test, y_test_pred)

    print()
    print("=" * 55)
    print("  Random Forest — Evaluation")
    print("=" * 55)
    print(f"  Training accuracy  : {train_acc:.4f}")
    print(f"  Test accuracy      : {test_acc:.4f}")
    print(f"  Test precision     : {test_prec:.4f}")
    print(f"  Test recall        : {test_rec:.4f}")
    print(f"  Test F1 score      : {test_f1:.4f}")
    print()
    print("  Confusion matrix (test):")
    print(f"    TN={cm[0,0]}  FP={cm[0,1]}")
    print(f"    FN={cm[1,0]}  TP={cm[1,1]}")
    print()
    print("  Classification report (test):")
    print(classification_report(y_test, y_test_pred,
                                 target_names=["normal(0)", "at_risk(1)"],
                                 zero_division=0))
    print("=" * 55)

    return {
        "train_accuracy": train_acc,
        "test_accuracy":  test_acc,
        "test_precision": test_prec,
        "test_recall":    test_rec,
        "test_f1":        test_f1,
        "confusion_matrix": cm.tolist(),
    }


# ===========================================================================
# Step 5 — AS-1047 validation inference
# ===========================================================================

def validate_as1047_inference(
    clf: RandomForestClassifier,
    feature_cols: list[str],
) -> float:
    """
    Run the REAL feature engineering pipeline on the demo dataset and
    pass AS-1047 / BRG-1047's engineered features to the trained model.

    This is the proof that:
        real sensor data  →  real features  →  real model inference
    No probability is hardcoded for AS-1047.

    Returns:
        failure_probability — the model's predict_proba output for AS-1047
    """
    logger.info("Running AS-1047 validation inference …")

    # Load the demo dataset (the 10-asset, 21-component CSV set)
    data       = load_and_prepare_data()
    feature_df = build_feature_dataset(data)

    brg_row = feature_df[feature_df["component_id"] == "BRG-1047"]
    if brg_row.empty:
        raise RuntimeError("BRG-1047 not found in demo feature dataset.")

    # Align feature columns to the exact training order
    X_as1047 = brg_row[feature_cols].values.astype(float)

    # predict_proba returns [[prob_class_0, prob_class_1]]
    proba            = clf.predict_proba(X_as1047)[0]
    failure_prob     = float(proba[1])   # probability of failure (class 1)
    predicted_class  = int(clf.predict(X_as1047)[0])
    risk_level       = (
        "HIGH"   if failure_prob >= 0.67 else
        "MEDIUM" if failure_prob >= 0.33 else
        "LOW"
    )

    print()
    print("=" * 55)
    print("  AS-1047 / BRG-1047 — Real Inference Validation")
    print("=" * 55)
    print(f"  failure_probability : {failure_prob:.4f}")
    print(f"  predicted_class     : {predicted_class}  (1 = at-risk)")
    print(f"  risk_level          : {risk_level}")
    print()
    print("  Source: predict_proba() on real engineered features")
    print("  No hardcoding. No asset_id rule.")
    print("=" * 55)

    return failure_prob


# ===========================================================================
# Main entry point
# ===========================================================================

def main() -> dict:
    print()
    print("AssetSentinel — Random Forest Training  (Member 2 / Selin)")
    print("=" * 55)

    # --- 1. Training data ---
    df = load_or_generate_training_data()
    pos = int(df["failure_label"].sum())
    neg = len(df) - pos
    print(f"  Training dataset   : {len(df)} rows")
    print(f"  Class distribution : failure=1: {pos}, failure=0: {neg}")
    print(f"  Feature columns    : {len(RF_FEATURE_NAMES)}")

    # --- 2. Prepare arrays ---
    X, y, feature_cols = prepare_training_arrays(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )
    print(f"  Train split        : {len(X_train)} rows")
    print(f"  Test split         : {len(X_test)} rows")

    # --- 3. Train ---
    clf = train_random_forest(X_train, y_train)

    # --- 4. Evaluate ---
    metrics = evaluate_model(clf, X_train, y_train, X_test, y_test)

    # --- 5. Save artifacts ---
    save_artifact(clf, RF_MODEL_PATH)
    save_feature_columns(feature_cols)
    print(f"\n  Model saved   : {RF_MODEL_PATH}")
    print(f"  Columns saved : {RF_MODEL_PATH.parent / 'feature_columns.json'}")

    # --- 6. AS-1047 inference validation ---
    as1047_prob = validate_as1047_inference(clf, feature_cols)
    metrics["as1047_failure_probability"] = as1047_prob

    return metrics


if __name__ == "__main__":
    main()
