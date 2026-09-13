from sqlalchemy import Column, String, Text, Float
from app.database import Base


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    maintenance_id = Column(String, primary_key=True, index=True)
    asset_id = Column(String, nullable=False, index=True)
    component_id = Column(String, nullable=False, index=True)
    maintenance_type = Column(String, nullable=False)
    maintenance_date = Column(String, nullable=False)   # ISO date string
    technician_action = Column(String, nullable=False)
    status = Column(String, nullable=False)             # COMPLETED | OVERDUE | SCHEDULED
    hours_since_service = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)
