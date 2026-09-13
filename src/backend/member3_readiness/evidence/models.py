"""
AssetSentinel — Evidence Layer: Canonical Models
Member 3 (Tisha) | src/backend/member3_readiness/evidence/models.py

Purpose:
    Defines the Pydantic models for:
      1. Canonical EvidenceObject — the ONLY decision-input source for the
         Readiness Engine, Maintenance Priority Engine, and IBM Bob.
      2. Typed input models for the non-ML evidence that the Evidence Builder
         requires: ComponentInfo and MaintenanceInfo.

Contract alignment:
    All field names, enum values, and structure follow exactly:
        src/backend/integration/contracts/data-contracts.md
    Sections 7, 9, 10 (Evidence), and 18 (Common Enums).

Ownership rules:
    - This file is owned by Member 3.
    - Do NOT import this file into Member 2 (would create circular dependency).
    - Do NOT add readiness_score, readiness_status, or any decision fields here.
    - Do NOT add component_id to EvidenceObject (contract §9/10 uses "component").
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Shared enum literals (contract §18)
# ---------------------------------------------------------------------------

CriticalityLevel = Literal["LOW", "MEDIUM", "HIGH"]
RiskLevel = Literal["LOW", "MEDIUM", "HIGH"]
AnomalySeverity = Literal["LOW", "MEDIUM", "HIGH"]
MaintenanceStatus = Literal["COMPLETED", "OVERDUE", "SCHEDULED"]
MissionImpactLevel = Literal["NONE", "LOW", "MEDIUM", "HIGH"]


# ---------------------------------------------------------------------------
# Sub-models for nested Evidence fields (contract §9/10)
# ---------------------------------------------------------------------------

class AnomalyEvidence(BaseModel):
    """
    Anomaly information nested inside EvidenceObject.

    Contract §10 defines:
        anomaly.sensor
        anomaly.severity

    anomaly_status (NORMAL/HIGH) is a Member 2 upstream field and is NOT
    part of the canonical EvidenceObject — it stays in the ML output only.
    """

    sensor: str = Field(
        ...,
        description=(
            "The sensor type exhibiting the anomaly. "
            "Allowed values: vibration, temperature, pressure, RPM, NONE. "
            "'NONE' is valid when anomaly_status is NORMAL."
        ),
    )
    severity: AnomalySeverity = Field(
        ...,
        description="Anomaly severity level: LOW | MEDIUM | HIGH (contract §18).",
    )


class MaintenanceEvidence(BaseModel):
    """
    Maintenance information nested inside EvidenceObject.

    Contract §10 defines:
        maintenance.hours_since_service
        maintenance.inspection_status
    """

    hours_since_service: float = Field(
        ...,
        ge=0.0,
        description="Hours elapsed since the last service/inspection for this component.",
    )
    inspection_status: MaintenanceStatus = Field(
        ...,
        description="Current inspection status: COMPLETED | OVERDUE | SCHEDULED (contract §7/18).",
    )


# ---------------------------------------------------------------------------
# Canonical EvidenceObject (contract §9/10)
# ---------------------------------------------------------------------------

class EvidenceObject(BaseModel):
    """
    Canonical evidence representation consumed by:
        - Readiness Engine
        - Maintenance Priority Engine
        - IBM Bob

    Field names are EXACT matches to data-contracts.md §10.

    IMPORTANT:
        - component_id is intentionally NOT included here (contract §10 uses
          "component" as the display/type name, not the raw ID).
        - No readiness fields (readiness_score, readiness_status, reasons).
        - No maintenance recommendation fields.
        - No ML training fields.
    """

    asset_id: str = Field(
        ...,
        description="Canonical asset identifier string (contract §3). Example: 'AS-1047'.",
    )
    component: str = Field(
        ...,
        description=(
            "Component display name / type from the component record "
            "(e.g. 'main_bearing', 'engine', 'hydraulics'). "
            "Mapped from component_type in ComponentInfo. "
            "contract §9/10 uses 'component', NOT 'component_id'."
        ),
    )
    failure_risk: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "Failure risk probability 0.0–1.0. "
            "Mapped from Member 2's failure_probability — same numeric value, "
            "different field name (Member 3 owns this name per contract §20). "
            "This is NOT RUL."
        ),
    )
    risk_level: RiskLevel = Field(
        ...,
        description="Risk level: LOW | MEDIUM | HIGH. Mapped from Member 2's risk_category.",
    )
    anomaly: AnomalyEvidence = Field(
        ...,
        description="Nested anomaly evidence (sensor, severity).",
    )
    maintenance: MaintenanceEvidence = Field(
        ...,
        description="Nested maintenance evidence (hours_since_service, inspection_status).",
    )
    criticality: CriticalityLevel = Field(
        ...,
        description="Component criticality: LOW | MEDIUM | HIGH (from component record, contract §5/18).",
    )
    mission_impact: MissionImpactLevel = Field(
        default="NONE",
        description=(
            "Mission-specific impact level: NONE | LOW | MEDIUM | HIGH. "
            "NONE for generic (non-mission-specific) evidence. "
            "Set to mission.criticality when the component is required by the mission."
        ),
    )

    @field_validator("failure_risk")
    @classmethod
    def validate_failure_risk(cls, v: float) -> float:
        """Explicit guard — Pydantic ge/le covers it, but keeps the error message clear."""
        if not (0.0 <= v <= 1.0):
            raise ValueError(
                f"failure_risk must be between 0.0 and 1.0 inclusive, got {v}. "
                "This is failure_probability from Member 2, not RUL."
            )
        return v


# ---------------------------------------------------------------------------
# Input models for non-ML evidence (typed interfaces for Member 1 / future DB)
# ---------------------------------------------------------------------------

class ComponentInfo(BaseModel):
    """
    Typed input carrying component metadata needed to assemble EvidenceObject.

    Maps to contract §5 (Component Contract).
    Member 1 / database layer will provide this; Member 2 cannot provide
    component_type from the ML output alone.

    Note: component_id is carried here (for matching) but is NOT forwarded
    into the canonical EvidenceObject — the builder uses component_type
    for the 'component' field.
    """

    component_id: str = Field(..., description="Canonical component ID (contract §3).")
    asset_id: str = Field(..., description="Parent asset ID (contract §3).")
    component_type: str = Field(
        ...,
        description=(
            "Human-readable component type (e.g. 'main_bearing', 'engine'). "
            "This becomes the 'component' field in EvidenceObject."
        ),
    )
    criticality: CriticalityLevel = Field(
        ...,
        description="Component criticality: LOW | MEDIUM | HIGH (contract §5/18).",
    )


class MaintenanceInfo(BaseModel):
    """
    Typed input carrying maintenance record information needed to assemble EvidenceObject.

    Maps to contract §7 (Maintenance Record Contract).

    hours_since_service is NOT in the raw contract §7 fields (those are the
    maintenance record fields), but it IS in contract §10 (Evidence Field Names)
    as maintenance.hours_since_service. The builder derives or receives it here.

    Member 2's feature_engineering.py already computes hours_since_service
    (= operating_hours - hours_at_last_service). For now this field is
    explicitly required so the Evidence Layer doesn't silently skip it.
    """

    maintenance_id: str = Field(..., description="Canonical maintenance record ID (contract §3).")
    asset_id: str = Field(..., description="Asset ID this record belongs to (contract §7).")
    component_id: str = Field(..., description="Component ID this record belongs to (contract §7).")
    maintenance_type: str = Field(..., description="Type of maintenance action (contract §7).")
    maintenance_date: datetime = Field(..., description="Date of maintenance record (contract §7).")
    status: MaintenanceStatus = Field(
        ...,
        description="Maintenance status: COMPLETED | OVERDUE | SCHEDULED (contract §7/18).",
    )
    hours_since_service: float = Field(
        ...,
        ge=0.0,
        description=(
            "Hours elapsed since last service. "
            "Derived from operating_hours - hours_at_last_service. "
            "Required for maintenance.hours_since_service in EvidenceObject (contract §10)."
        ),
    )
    technician_action: Optional[str] = Field(
        default=None,
        description="Optional technician notes (contract §7 field: technician_action).",
    )
    notes: Optional[str] = Field(
        default=None,
        description="Optional free-text notes (contract §7 field: notes).",
    )
