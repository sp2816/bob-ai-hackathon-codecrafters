"""
AssetSentinel — Mission Models
Member 3 (Tisha) | src/backend/member3_readiness/missions/models.py
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field

# Using Literal for criticality per contract §11 and §18
MissionCriticality = Literal["LOW", "MEDIUM", "HIGH"]


class MissionInfo(BaseModel):
    """
    Canonical mission representation.
    Matches contract §11 exactly.
    """
    mission_id: str = Field(..., description="Canonical mission identifier")
    mission_name: str = Field(..., description="Mission display name")
    mission_type: str = Field(..., description="Mission type/category")
    criticality: MissionCriticality = Field(..., description="Mission criticality (LOW/MEDIUM/HIGH)")
    scheduled_time: datetime = Field(..., description="Scheduled execution time")
    required_components: list[str] = Field(
        default_factory=list,
        description="List of component types required for this mission"
    )
    readiness_threshold: Optional[float] = Field(
        default=None,
        description="Optional mission-specific hard threshold for readiness score"
    )
