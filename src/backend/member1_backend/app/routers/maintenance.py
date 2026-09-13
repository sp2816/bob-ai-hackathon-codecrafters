from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.maintenance_record import MaintenanceRecordResponse
from app.schemas.maintenance_recommendation import MaintenanceRecommendationResponse
from app.models.maintenance_recommendation import MaintenanceRecommendation
from app.services import maintenance_service

router = APIRouter(prefix="/maintenance", tags=["maintenance"])


@router.get("/recommendations", response_model=List[MaintenanceRecommendationResponse])
def list_maintenance_recommendations(db: Session = Depends(get_db)):
    """Return all ranked maintenance recommendations."""
    return db.query(MaintenanceRecommendation).order_by(MaintenanceRecommendation.priority.asc()).all()


@router.get("/{asset_id}", response_model=List[MaintenanceRecordResponse])
def list_maintenance_for_asset(asset_id: str, db: Session = Depends(get_db)):
    return maintenance_service.get_maintenance_by_asset(db, asset_id)


@router.get("/component/{component_id}", response_model=List[MaintenanceRecordResponse])
def list_maintenance_for_component(component_id: str, db: Session = Depends(get_db)):
    return maintenance_service.get_maintenance_by_component(db, component_id)
