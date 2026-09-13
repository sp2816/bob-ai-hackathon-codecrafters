from typing import Optional
from pydantic import BaseModel


class ComponentBase(BaseModel):
    component_id: str
    asset_id: str
    component_type: str
    criticality: str             # LOW | MEDIUM | HIGH
    installation_date: Optional[str] = None
    operating_hours: float
    life_limit: Optional[float] = None


class ComponentCreate(ComponentBase):
    pass


class ComponentResponse(ComponentBase):
    model_config = {"from_attributes": True}
