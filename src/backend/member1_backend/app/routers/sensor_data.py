from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.sensor_data import SensorDataResponse
from app.services import sensor_service

router = APIRouter(prefix="/sensor-data", tags=["sensor-data"])


@router.get("/{asset_id}", response_model=List[SensorDataResponse])
def list_sensor_data_for_asset(asset_id: str, db: Session = Depends(get_db)):
    return sensor_service.get_sensor_data_by_asset(db, asset_id)


@router.get("/component/{component_id}", response_model=List[SensorDataResponse])
def list_sensor_data_for_component(component_id: str, db: Session = Depends(get_db)):
    return sensor_service.get_sensor_data_by_component(db, component_id)
