from typing import List, Optional
from pydantic import BaseModel


class MissionBase(BaseModel):
    mission_id: str
    mission_name: str
    mission_type: str
    criticality: str                        # LOW | MEDIUM | HIGH
    scheduled_time: Optional[str] = None    # ISO datetime string
    required_components: Optional[List[str]] = None
    readiness_threshold: float = 0.66


class MissionCreate(MissionBase):
    pass


class MissionResponse(BaseModel):
    mission_id: str
    mission_name: str
    mission_type: str
    criticality: str
    scheduled_time: Optional[str] = None
    required_components: Optional[List[str]] = None
    readiness_threshold: float

    model_config = {"from_attributes": True}
