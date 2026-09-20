from pydantic import BaseModel
from typing import Optional


class CostAssumptionBase(BaseModel):
    component_type: str
    inspection_cost: float
    repair_cost: float
    replacement_cost: float
    failure_impact_cost: float
    monitoring_cost_traditional: float = 0.0
    inspection_cost_traditional: float = 0.0
    preventive_maintenance_traditional: float = 0.0
    sensor_data_cost_assetsentinel: float = 0.0
    assetsentinel_deployment_cost: float = 0.0
    residual_failure_probability_multiplier: float = 0.10
    emergency_intervention_cost: float = 0.0
    emergency_maintenance_cost: float = 0.0
    downtime_cost_per_hour: float = 0.0
    planned_downtime_hours: float = 0.0
    emergency_downtime_hours: float = 0.0
    mission_disruption_cost: float = 0.0

class CostAssumptionCreate(CostAssumptionBase):
    pass

class CostAssumptionResponse(CostAssumptionBase):
    class Config:
        from_attributes = True
