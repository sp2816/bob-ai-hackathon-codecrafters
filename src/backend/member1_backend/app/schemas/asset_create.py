"""
AssetSentinel — Add Asset Pydantic Schemas
src/backend/member1_backend/app/schemas/asset_create.py

Defines the request and response bodies for POST /assets/ (Add Asset & Analyze).
Mirrors the frontend AssetCreateRequest / AssetCreateResponse TypeScript interfaces.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Enums / Literals
# ---------------------------------------------------------------------------

SensorCondition = Literal["NORMAL", "DEGRADING", "CRITICAL"]
Criticality     = Literal["LOW", "MEDIUM", "HIGH"]
MaintenanceStatus = Literal["COMPLETED", "OVERDUE", "SCHEDULED"]
MaintenanceType   = Literal["inspection", "service", "repair"]


# ---------------------------------------------------------------------------
# Request sub-models
# ---------------------------------------------------------------------------

class ComponentInput(BaseModel):
    """One component associated with the new asset."""
    component_id:           str   = Field(..., description="Unique component ID, e.g. BRG-2001")
    component_type:         str   = Field(..., description="Type, e.g. main_bearing | engine | hydraulics")
    criticality:            Criticality
    operating_hours:        float = Field(..., ge=0.0, description="Total operating hours")
    life_limit:             Optional[float] = Field(None, ge=0.0, description="Rated life in hours")
    service_interval_hours: float = Field(..., gt=0.0, description="Hours between required services (for ML)")
    installation_date:      Optional[str] = Field(None, description="ISO date YYYY-MM-DD")


class SensorInput(BaseModel):
    """
    Current sensor readings plus a synthetic condition profile.

    The condition profile drives a deterministic 20-reading observation window
    used by the ML feature pipeline. This is an explicit synthetic input
    (labeled as such in the UI) — not historical telemetry.
    """
    condition:   SensorCondition = Field(..., description="Synthetic condition profile: NORMAL | DEGRADING | CRITICAL")
    vibration:   float = Field(..., ge=0.0, le=50.0,   description="Vibration mm/s RMS")
    temperature: float = Field(..., ge=0.0, le=200.0,  description="Temperature °C")
    pressure:    float = Field(..., ge=0.0, le=500.0,  description="Pressure bar")
    RPM:         float = Field(..., ge=0.0, le=20000.0, description="Rotational speed RPM")


class MaintenanceInput(BaseModel):
    """Maintenance record for the new asset's component."""
    maintenance_type:    MaintenanceType
    maintenance_date:    str   = Field(..., description="ISO date YYYY-MM-DD of last service")
    technician_action:   str   = Field(..., min_length=3)
    status:              MaintenanceStatus
    hours_since_service: float = Field(..., ge=0.0, description="Hours elapsed since last service")
    notes:               Optional[str] = None


class AssetCreateRequest(BaseModel):
    """
    Full operator input for adding a new asset and running the complete
    ML → Evidence → Readiness → Maintenance analysis pipeline.
    """
    # Asset fields (mirrors Asset SQLite model)
    asset_id:          str   = Field(..., min_length=1, description="Unique asset ID, e.g. AS-2001")
    asset_name:        str   = Field(..., min_length=1)
    asset_type:        str   = Field(..., description="e.g. aircraft | rotary_wing | ground_vehicle")
    unit:              str   = Field(..., description="Operational unit, e.g. Unit-Alpha")
    operational_hours: float = Field(..., ge=0.0)

    # Subsystems
    component:   ComponentInput
    sensors:     SensorInput
    maintenance: MaintenanceInput

    @model_validator(mode="after")
    def validate_hours_consistency(self) -> "AssetCreateRequest":
        """hours_since_service must not exceed operating_hours."""
        if self.maintenance.hours_since_service > self.component.operating_hours:
            raise ValueError(
                "hours_since_service cannot exceed the component's operating_hours. "
                f"Got hours_since_service={self.maintenance.hours_since_service} > "
                f"operating_hours={self.component.operating_hours}."
            )
        return self


# ---------------------------------------------------------------------------
# Response sub-models
# ---------------------------------------------------------------------------

class PredictionSummary(BaseModel):
    prediction_id:       str
    failure_probability: float
    risk_category:       str   # LOW | MEDIUM | HIGH

    model_config = {"from_attributes": True}


class AnomalySummary(BaseModel):
    anomaly_id:       str
    anomaly_status:   str  # NORMAL | HIGH
    anomaly_severity: str  # LOW | MEDIUM | HIGH
    sensor:           str  # vibration | temperature | pressure | RPM | NONE

    model_config = {"from_attributes": True}


class ReadinessSummary(BaseModel):
    readiness_status: str    # READY | CONDITIONALLY_READY | NOT_READY
    readiness_score:  float
    reasons:          list[str]


class RecommendationSummary(BaseModel):
    recommendation_id: str
    action:            str
    priority:          int
    urgency:           str  # LOW | MEDIUM | HIGH
    risk:              str
    decision:          Optional[str] = None
    economic_impact:   Optional[dict] = None


class AssetCreateResponse(BaseModel):
    """
    Full analysis result returned after Add Asset & Analyze completes.
    All values come from the backend pipeline — none are fabricated.
    """
    asset:          dict                        # AssetResponse fields
    prediction:     PredictionSummary
    anomaly:        AnomalySummary
    readiness:      ReadinessSummary
    recommendation: Optional[RecommendationSummary] = None
    pipeline_note:  str = "Single-component inference completed. No fleet rerun performed."
