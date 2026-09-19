from pydantic import BaseModel
from typing import Optional


class MaintenanceRecommendationBase(BaseModel):
    recommendation_id: str
    asset_id: str
    component_id: str
    priority: int                   # 1 = highest
    action: str
    reason: Optional[str] = None
    risk: str                       # LOW | MEDIUM | HIGH
    mission_impact: str             # LOW | MEDIUM | HIGH
    urgency: str                    # LOW | MEDIUM | HIGH
    status: str = "OPEN"            # OPEN | IN_PROGRESS | RESOLVED
    decision: Optional[str] = None
    economic_impact: Optional[dict] = None
    timeline: Optional[list] = None



class MaintenanceRecommendationCreate(MaintenanceRecommendationBase):
    pass


class MaintenanceRecommendationResponse(MaintenanceRecommendationBase):
    model_config = {"from_attributes": True}
