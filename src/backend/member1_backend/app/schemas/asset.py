from typing import Optional
from pydantic import BaseModel


class AssetBase(BaseModel):
    asset_id: str
    asset_name: str
    asset_type: str
    unit: str
    operational_hours: float
    current_status: str          # READY | CONDITIONALLY_READY | NOT_READY
    readiness_score: Optional[float] = None


class AssetCreate(AssetBase):
    pass


class AssetResponse(AssetBase):
    model_config = {"from_attributes": True}
