"""
AssetSentinel — Maintenance Priority Engine: Models
Member 3 (Tisha) | src/backend/member3_readiness/maintenance/models.py

Purpose:
    Defines the output model for the Maintenance Priority Engine:
        MaintenanceRecommendation — a single ranked maintenance action.

Contract alignment:
    Field names follow data-contracts.md §16 (Maintenance Priority Contract)
    and §17 (Maintenance Recommendation Example).

Ownership rules:
    - Only Member 3 modifies this file.
    - Member 1 wraps MaintenanceRecommendation in API response schemas.
    - Member 4 renders the ranked list in the Maintenance Priority Plan page.
    - Do NOT add readiness or mission-verdict fields here.
    - IBM Bob uses these recommendations via MCP to explain priorities.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from member3_readiness.evidence.models import CriticalityLevel, MissionImpactLevel, RiskLevel

# Allowed recommendation status values (contract §18)
RecommendationStatus = Literal["OPEN", "IN_PROGRESS", "RESOLVED"]

# Urgency level (derived from maintenance_status and mission timing)
UrgencyLevel = Literal["LOW", "MEDIUM", "HIGH"]


class MaintenanceRecommendation(BaseModel):
    """
    A single ranked maintenance recommendation produced by the Maintenance
    Priority Engine.

    Contract §16/17 canonical fields:
        recommendation_id  — unique identifier for this recommendation
        asset_id           — asset that needs maintenance
        component_id       — component that needs maintenance
        component          — component display name (e.g. 'main_bearing')
        priority           — integer rank (1 = highest priority)
        priority_score     — float 0.0–1.0 driving the rank (higher = more urgent)
        action             — human-readable action description
        reason             — human-readable explanation of the ranking
        risk               — risk level: LOW | MEDIUM | HIGH
        mission_impact     — mission impact: NONE | LOW | MEDIUM | HIGH
        urgency            — urgency level: LOW | MEDIUM | HIGH
        status             — recommendation status: OPEN | IN_PROGRESS | RESOLVED

    The priority rank MUST emerge from the actual priority calculation —
    never hardcode AS-1047 as rank 1 (contract §17).
    """

    recommendation_id: str = Field(
        ...,
        description="Unique identifier for this recommendation (contract §3). Example: 'REC-001'.",
    )
    asset_id: str = Field(
        ...,
        description="Asset that requires maintenance (contract §3). Example: 'AS-1047'.",
    )
    component_id: str = Field(
        ...,
        description="Component that requires maintenance (contract §3). Example: 'BRG-1047'.",
    )
    component: str = Field(
        ...,
        description="Component display name/type (e.g. 'main_bearing'). Same as EvidenceObject.component.",
    )
    priority: int = Field(
        ...,
        ge=1,
        description="Integer rank within the fleet-wide maintenance list. 1 = highest priority.",
    )
    priority_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "Computed priority score 0.0–1.0 that determines rank ordering. "
            "Higher score = higher priority (rank closer to 1). "
            "Formula: w1×failure_risk + w2×criticality + w3×mission_impact + w4×urgency."
        ),
    )
    action: str = Field(
        ...,
        description="Human-readable maintenance action. Example: 'Inspect and replace bearing'.",
    )
    reason: str = Field(
        ...,
        description=(
            "Human-readable explanation of why this component was ranked at this priority. "
            "Must reference the contributing factors."
        ),
    )
    risk: RiskLevel = Field(
        ...,
        description="Component risk level: LOW | MEDIUM | HIGH.",
    )
    mission_impact: MissionImpactLevel = Field(
        ...,
        description="Mission impact level: NONE | LOW | MEDIUM | HIGH.",
    )
    urgency: UrgencyLevel = Field(
        ...,
        description="Urgency level: LOW | MEDIUM | HIGH (derived from maintenance status).",
    )
    status: RecommendationStatus = Field(
        default="OPEN",
        description="Recommendation status: OPEN | IN_PROGRESS | RESOLVED.",
    )
