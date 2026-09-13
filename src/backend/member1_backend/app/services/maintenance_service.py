from sqlalchemy.orm import Session
from app.models.maintenance_record import MaintenanceRecord
from app.schemas.maintenance_record import MaintenanceRecordCreate


def get_maintenance_by_asset(db: Session, asset_id: str):
    return db.query(MaintenanceRecord).filter(MaintenanceRecord.asset_id == asset_id).all()


def get_maintenance_by_component(db: Session, component_id: str):
    return (
        db.query(MaintenanceRecord)
        .filter(MaintenanceRecord.component_id == component_id)
        .all()
    )


def create_maintenance_record(db: Session, record: MaintenanceRecordCreate):
    db_record = MaintenanceRecord(**record.model_dump())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record
