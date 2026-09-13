from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.maintenance_record import MaintenanceRecord
from app.schemas.maintenance_record import MaintenanceRecordCreate, MaintenanceRecordResponse
from app.services import maintenance_service

router = APIRouter(prefix="/maintenance-records", tags=["maintenance-records"])


@router.get("/{asset_id}", response_model=List[MaintenanceRecordResponse])
def list_maintenance_records(asset_id: str, db: Session = Depends(get_db)):
    """Return all maintenance records for a given asset."""
    return maintenance_service.get_maintenance_by_asset(db, asset_id)


@router.get("/component/{component_id}", response_model=List[MaintenanceRecordResponse])
def list_maintenance_records_by_component(component_id: str, db: Session = Depends(get_db)):
    """Return all maintenance records for a given component."""
    return maintenance_service.get_maintenance_by_component(db, component_id)


@router.post("/", response_model=MaintenanceRecordResponse, status_code=201)
def create_maintenance_record(
    record: MaintenanceRecordCreate,
    db: Session = Depends(get_db),
):
    """Upload a new maintenance record."""
    existing = db.get(MaintenanceRecord, record.maintenance_id)
    if existing:
        raise HTTPException(status_code=409, detail="maintenance_id already exists")
    return maintenance_service.create_maintenance_record(db, record)
