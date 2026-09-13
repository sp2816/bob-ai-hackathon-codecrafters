from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel


class ReadinessResultBase(BaseModel):
    result_id: str
    asset_id: str
    mission_id: Optional[str] = None
    readiness_score: float
    readiness_status: str                           # READY | CONDITIONALLY_READY | NOT_READY
    reasons: Optional[List[str]] = None
    evidence: Optional[Union[List[Dict[str, Any]], Dict[str, Any]]] = None
    timestamp: str                                  # ISO datetime string


class ReadinessResultCreate(ReadinessResultBase):
    pass


class ReadinessResultResponse(ReadinessResultBase):
    model_config = {"from_attributes": True}
