"""
AssetSentinel — Cost Engine
Member 3 (Tisha) | src/backend/member3_readiness/maintenance/cost_engine.py

Calculates Modeled Economic Benefit and Potentially Avoidable Cost based on
configured Demo Assumptions.
"""
from typing import Dict, Any

def calculate_costs(
    failure_probability: float,
    decision: str,
    urgency: str,
    cost_assumptions: Dict[str, float],
    mission_impact_level: str
) -> Dict[str, Any]:
    """
    Calculates counterfactual economic scenarios with detailed breakdown:
    - WITHOUT AssetSentinel (Traditional Cost)
    - WITH AssetSentinel (AssetSentinel Operating Cost)
    """
    
    # Base params
    downtime_per_hour = cost_assumptions.get("downtime_cost_per_hour", 0.0)
    deployment_cost = cost_assumptions.get("assetsentinel_deployment_cost", 0.0)
    
    # 1. TRADITIONAL SCENARIO (WITHOUT ASSETSENTINEL)
    trad_monitoring = cost_assumptions.get("monitoring_cost_traditional", 0.0)
    trad_inspection = cost_assumptions.get("inspection_cost_traditional", 0.0)
    trad_prev_maint = cost_assumptions.get("preventive_maintenance_traditional", 0.0)
    
    emergency_intervention = cost_assumptions.get("emergency_intervention_cost", 0.0)
    emergency_maintenance = cost_assumptions.get("emergency_maintenance_cost", 0.0)
    emergency_downtime = cost_assumptions.get("emergency_downtime_hours", 0.0)
    
    mission_disruption = 0.0
    if mission_impact_level in ["LOW", "MEDIUM", "HIGH"]:
        mission_disruption = cost_assumptions.get("mission_disruption_cost", 0.0)

    emergency_downtime_cost = emergency_downtime * downtime_per_hour
    failure_scenario_cost = emergency_intervention + emergency_maintenance + emergency_downtime_cost + mission_disruption
    
    expected_reactive_failure_cost = failure_probability * failure_scenario_cost
    
    traditional_total = trad_monitoring + trad_inspection + trad_prev_maint + expected_reactive_failure_cost

    # 2. ASSETSENTINEL SCENARIO
    as_sensor_data = cost_assumptions.get("sensor_data_cost_assetsentinel", 0.0)
    
    planned_inspection_cost = 0.0
    planned_intervention_cost = 0.0
    planned_downtime_cost = 0.0
    
    # The timeline determines whether we suffer emergency downtime or planned downtime.
    # AssetSentinel early detection allows for planned downtime even if urgency is HIGH.
    downtime_hours = cost_assumptions.get("planned_downtime_hours", 0.0)

    if decision == "REPAIR":
        planned_intervention_cost = cost_assumptions.get("repair_cost", 0.0)
        planned_downtime_cost = downtime_hours * downtime_per_hour
    elif decision == "REPLACE":
        planned_intervention_cost = cost_assumptions.get("replacement_cost", 0.0)
        planned_downtime_cost = downtime_hours * downtime_per_hour
    elif decision == "INSPECT_FIRST":
        planned_inspection_cost = cost_assumptions.get("inspection_cost", 0.0)
        # Assume a minimal downtime for inspection
        planned_downtime_cost = 2.0 * downtime_per_hour
        
    # Residual failure risk (e.g. 10% remains even with AssetSentinel)
    residual_multiplier = cost_assumptions.get("residual_failure_probability_multiplier", 0.10)
    residual_failure_cost = (failure_probability * residual_multiplier) * failure_scenario_cost
    
    as_total = as_sensor_data + planned_inspection_cost + planned_intervention_cost + planned_downtime_cost + residual_failure_cost

    # 3. SAVINGS AND ROI
    potential_cost_avoided = traditional_total - as_total
    net_economic_benefit = potential_cost_avoided - deployment_cost
    roi_percent = (net_economic_benefit / deployment_cost * 100) if deployment_cost > 0 else 0.0

    return {
        "traditional": {
            "monitoring_cost": trad_monitoring,
            "inspection_cost": trad_inspection,
            "preventive_maintenance_cost": trad_prev_maint,
            "expected_reactive_failure_cost": expected_reactive_failure_cost,
            "total": traditional_total
        },
        "assetsentinel": {
            "sensor_data_cost": as_sensor_data,
            "planned_inspection_cost": planned_inspection_cost,
            "planned_intervention_cost": planned_intervention_cost,
            "planned_downtime_cost": planned_downtime_cost,
            "residual_failure_cost": residual_failure_cost,
            "total": as_total
        },
        "potential_cost_avoided": potential_cost_avoided,
        "deployment_cost": deployment_cost,
        "net_economic_benefit": net_economic_benefit,
        "roi_percent": roi_percent
    }
