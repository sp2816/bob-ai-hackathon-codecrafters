from typing import Optional
from pydantic import BaseModel


class MaintenanceRecordBase(BaseModel):
    maintenance_id: str
    asset_id: str
    component_id: str
    maintenance_type: str
    maintenance_date: str        # ISO date string
    technician_action: str
    status: str                  # COMPLETED | OVERDUE | SCHEDULED
    notes: Optional[str] = None


class MaintenanceRecordCreate(MaintenanceRecordBase):
    pass


class MaintenanceRecordResponse(MaintenanceRecordBase):
    model_config = {"from_attributes": True}
