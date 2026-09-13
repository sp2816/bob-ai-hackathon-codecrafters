"""
AssetSentinel — Train Isolation Forest
Member 2 (Selin) | src/backend/member2_ml/models/train_isolation_forest.py

Purpose:
    Trains an Isolation Forest anomaly detection model on engineered historical 
    sensor behaviour features (e.g., rolling_mean, trend_slope, max_z_score).
    
    Training Strategy (Option B):
    - Excludes known anomalous components (like AS-1047/BRG-1047) from the training set.
    - Uses the distribution of the remaining normal components to generate 
      additional synthetic normal sensor-behaviour profiles (n=1000).
    - Trains Isolation Forest on this robust dataset of normal behavior.
    - Saves the trained model and the exact feature column order for inference.
"""

import logging
import numpy as np
from sklearn.ensemble import IsolationForest

from features.feature_engineering import run_feature_pipeline
from models.model_utils import save_artifact, save_feature_columns, IF_MODEL_PATH, IF_FEATURE_COLS_PATH

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def train_isolation_forest(contamination: float = 0.05, random_state: int = 42) -> IsolationForest:
    logger.info("Starting Isolation Forest training pipeline...")

    # Extract features using the existing pipeline
    _, rf_result, if_result = run_feature_pipeline()

    X = if_result.X
    feature_names = if_result.feature_names
    meta = if_result.meta

    # Identify AS-1047 / BRG-1047 and exclude it from training
    is_as1047 = (meta["asset_id"] == "AS-1047") & (meta["component_id"] == "BRG-1047")
    
    # Exclude at-risk components based on Random Forest training labels (y=1) to establish a clean normal baseline
    is_normal = (rf_result.y == 0) & (~is_as1047)

    X_normal = X[is_normal]
    
    # Generate synthetic normal profiles based on the distribution of normal components
    np.random.seed(random_state)
    normal_means = np.mean(X_normal, axis=0)
    normal_stds = np.std(X_normal, axis=0)
    
    n_synthetic = 1000
    # Add a small epsilon to standard deviation to prevent zero variance in purely constant features
    X_synthetic = np.random.normal(loc=normal_means, scale=normal_stds + 1e-6, size=(n_synthetic, X.shape[1]))
    
    # Combine original normal rows with synthetic normal rows
    X_train = np.vstack([X_normal, X_synthetic])

    logger.info(f"Training Isolation Forest with {X_train.shape[0]} normal samples (original={X_normal.shape[0]}, synthetic={n_synthetic}) and {X_train.shape[1]} features.")
    
    model = IsolationForest(
        n_estimators=100,
        contamination=contamination,
        random_state=random_state,
        n_jobs=-1
    )
    
    model.fit(X_train)
    
    # Evaluate AS-1047 BRG-1047 to ensure it produces a genuine anomaly result without being in the training set
    if is_as1047.any():
        X_as1047 = X[is_as1047]
        anomaly_scores = model.decision_function(X_as1047)
        anomaly_status = model.predict(X_as1047)
        
        logger.info(f"Canonical Asset AS-1047 / BRG-1047 Inference Result (Unseen during training):")
        logger.info(f"  Anomaly Score: {anomaly_scores[0]:.4f}")
        logger.info(f"  Anomaly Status (1=Normal, -1=Anomaly): {anomaly_status[0]}")
    else:
        logger.warning("AS-1047 / BRG-1047 not found in dataset.")

    # Evaluate a normal component
    if is_normal.any():
        idx_normal = np.where(is_normal)[0][0]
        X_norm_sample = X[idx_normal:idx_normal+1]
        norm_score = model.decision_function(X_norm_sample)[0]
        norm_status = model.predict(X_norm_sample)[0]
        row_meta = meta.iloc[idx_normal]
        logger.info(f"Normal Asset {row_meta['asset_id']} / {row_meta['component_id']} Inference Result:")
        logger.info(f"  Anomaly Score: {norm_score:.4f}")
        logger.info(f"  Anomaly Status (1=Normal, -1=Anomaly): {norm_status}")

    # Save artifacts
    save_artifact(model, IF_MODEL_PATH)
    save_feature_columns(feature_names, IF_FEATURE_COLS_PATH)

    logger.info("Isolation Forest training complete and artifacts saved.")
    
    return model

if __name__ == "__main__":
    train_isolation_forest()
