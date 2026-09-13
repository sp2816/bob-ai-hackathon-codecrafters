"""
AssetSentinel — Model Utilities
Member 2 (Selin) | src/backend/member2_ml/models/model_utils.py

Purpose:
    Shared helpers for saving, loading, and inspecting model artifacts.
    Both train_random_forest.py (Phase 4) and predict.py (Phase 5) use
    these utilities so artifact paths and formats stay consistent.

Artifacts produced by training:
    models/artifacts/random_forest_model.joblib
    models/artifacts/feature_columns.json

The feature_columns.json file records the EXACT column order used at
training time. Inference MUST load and apply the same column order to
avoid silent feature-position errors.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import joblib

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Canonical artifact paths — relative to this file's parent directory
# ---------------------------------------------------------------------------
_MODELS_DIR     = Path(__file__).resolve().parent          # …/member2_ml/models/
ARTIFACTS_DIR   = _MODELS_DIR / "artifacts"

RF_MODEL_PATH        = ARTIFACTS_DIR / "random_forest_model.joblib"
FEATURE_COLS_PATH    = ARTIFACTS_DIR / "feature_columns.json"
IF_MODEL_PATH        = ARTIFACTS_DIR / "isolation_forest_model.joblib"  # Phase 5
IF_FEATURE_COLS_PATH = ARTIFACTS_DIR / "isolation_feature_columns.json" # Phase 5


def save_artifact(obj: Any, path: Path) -> None:
    """Serialise obj to path using joblib."""
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(obj, path)
    logger.info("Saved artifact: %s", path)


def load_artifact(path: Path) -> Any:
    """Load a joblib artifact from path."""
    if not path.exists():
        raise FileNotFoundError(
            f"Model artifact not found: {path}\n"
            "Run models/train_random_forest.py first."
        )
    obj = joblib.load(path)
    logger.info("Loaded artifact: %s", path)
    return obj


def save_feature_columns(columns: list[str], path: Path = FEATURE_COLS_PATH) -> None:
    """
    Persist the ordered list of feature column names used during training.

    This is the SINGLE SOURCE OF TRUTH for feature order.
    Inference code MUST load this list and reorder its feature matrix
    accordingly before calling model.predict_proba().
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"feature_columns": columns}, f, indent=2)
    logger.info("Saved feature columns (%d) → %s", len(columns), path)


def load_feature_columns(path: Path = FEATURE_COLS_PATH) -> list[str]:
    """
    Load the saved feature column order.
    Raises FileNotFoundError if artifacts have not been generated yet.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"Feature columns file not found: {path}\n"
            "Run models/train_random_forest.py first."
        )
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    cols = data["feature_columns"]
    logger.info("Loaded %d feature columns from %s", len(cols), path)
    return cols


def artifacts_exist() -> bool:
    """Return True only when both the model and feature-columns files exist."""
    return RF_MODEL_PATH.exists() and FEATURE_COLS_PATH.exists()
