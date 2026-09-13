"""
Predictions router — exposes stored ML prediction and anomaly data.
Owner: Member 1 (backend/API layer).
Member 2 owns the ML computation; these routes serve the persisted results.
"""
import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.prediction import Prediction
from app.models.anomaly import Anomaly

router = APIRouter(prefix="/predictions", tags=["predictions"])


class PredictionResponse(BaseModel):
    prediction_id: str
    asset_id: str
    component_id: str
    failure_probability: float
    risk_category: str  # LOW | MEDIUM | HIGH
    timestamp: str

    model_config = {"from_attributes": True}


class AnomalyResponse(BaseModel):
    anomaly_id: str
    asset_id: str
    component_id: str
    anomaly_score: float
    anomaly_status: str   # NORMAL | HIGH
    anomaly_severity: str  # LOW | MEDIUM | HIGH
    sensor: str
    timestamp: str

    model_config = {"from_attributes": True}


@router.get("/", response_model=List[PredictionResponse], summary="List all stored ML predictions")
def list_predictions(db: Session = Depends(get_db)):
    """Return all stored failure predictions from Member 2's ML pipeline."""
    return db.query(Prediction).order_by(Prediction.timestamp.desc()).all()


@router.get("/asset/{asset_id}", response_model=List[PredictionResponse], summary="Predictions for a specific asset")
def list_predictions_for_asset(asset_id: str, db: Session = Depends(get_db)):
    """Return all stored failure predictions for a specific asset."""
    return (
        db.query(Prediction)
        .filter(Prediction.asset_id == asset_id)
        .order_by(Prediction.timestamp.desc())
        .all()
    )


@router.get("/anomalies", response_model=List[AnomalyResponse], summary="List all stored anomaly detections")
def list_anomalies(db: Session = Depends(get_db)):
    """Return all stored anomaly detections from Member 2's Isolation Forest."""
    return db.query(Anomaly).order_by(Anomaly.timestamp.desc()).all()


@router.get("/anomalies/asset/{asset_id}", response_model=List[AnomalyResponse], summary="Anomalies for a specific asset")
def list_anomalies_for_asset(asset_id: str, db: Session = Depends(get_db)):
    """Return all stored anomaly detections for a specific asset."""
    return (
        db.query(Anomaly)
        .filter(Anomaly.asset_id == asset_id)
        .order_by(Anomaly.timestamp.desc())
        .all()
    )
