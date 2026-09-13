from sqlalchemy.orm import Session
from app.models.sensor_data import SensorData
from app.schemas.sensor_data import SensorDataCreate


def get_sensor_data_by_asset(db: Session, asset_id: str):
    return db.query(SensorData).filter(SensorData.asset_id == asset_id).all()


def get_sensor_data_by_component(db: Session, component_id: str):
    return db.query(SensorData).filter(SensorData.component_id == component_id).all()


def create_sensor_data(db: Session, sensor_data: SensorDataCreate):
    db_sensor = SensorData(**sensor_data.model_dump())
    db.add(db_sensor)
    db.commit()
    db.refresh(db_sensor)
    return db_sensor
