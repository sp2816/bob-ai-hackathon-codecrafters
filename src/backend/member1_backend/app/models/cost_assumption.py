from sqlalchemy import Column, String, Float
from app.database import Base


class CostAssumption(Base):
    """
    Stores configurable demo cost assumptions per component type.
    These are MODELED DEMO ASSUMPTIONS, not real military costs.
    """
    __tablename__ = "cost_assumptions"

    component_type = Column(String, primary_key=True, index=True)
    inspection_cost = Column(Float, nullable=False, default=0.0)
    repair_cost = Column(Float, nullable=False, default=0.0)
    replacement_cost = Column(Float, nullable=False, default=0.0)
    failure_impact_cost = Column(Float, nullable=False, default=0.0)
    
    # Counterfactual economic model parameters
    monitoring_cost_traditional = Column(Float, nullable=False, default=0.0)
    inspection_cost_traditional = Column(Float, nullable=False, default=0.0)
    preventive_maintenance_traditional = Column(Float, nullable=False, default=0.0)
    
    sensor_data_cost_assetsentinel = Column(Float, nullable=False, default=0.0)
    assetsentinel_deployment_cost = Column(Float, nullable=False, default=0.0)
    
    # 0.10 means 10% residual failure risk remaining after intervention (demo assumption)
    residual_failure_probability_multiplier = Column(Float, nullable=False, default=0.10)
    
    # Base emergency vs planned parameters
    emergency_intervention_cost = Column(Float, nullable=False, default=0.0)
    emergency_maintenance_cost = Column(Float, nullable=False, default=0.0)
    downtime_cost_per_hour = Column(Float, nullable=False, default=0.0)
    planned_downtime_hours = Column(Float, nullable=False, default=0.0)
    emergency_downtime_hours = Column(Float, nullable=False, default=0.0)
    mission_disruption_cost = Column(Float, nullable=False, default=0.0)
