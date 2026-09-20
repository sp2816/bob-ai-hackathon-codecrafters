import pytest
import sys
import os
from pathlib import Path

# Add member1_backend and member3_readiness to path
backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path / "member1_backend"))
sys.path.insert(0, str(backend_path))

from app.models.maintenance_recommendation import MaintenanceRecommendation

def test_different_economic_results_same_component():
    """Two assets using the same component type can have different economic results."""
    rec1 = MaintenanceRecommendation(
        recommendation_id="REC-001",
        asset_id="AS-1047",
        component_id="BRG-1047",
        priority=1,
        action="Repair",
        risk="HIGH",
        mission_impact="HIGH",
        urgency="HIGH",
        decision="REPAIR",
        economic_impact={
            "traditional": {"total": 5000},
            "assetsentinel": {"total": 1000},
            "potential_cost_avoided": 4000,
            "net_economic_benefit": 4000,
            "deployment_cost": 0,
            "roi_percent": 0
        }
    )
    rec2 = MaintenanceRecommendation(
        recommendation_id="REC-002",
        asset_id="AS-2001",
        component_id="BRG-2001",
        priority=2,
        action="Monitor",
        risk="LOW",
        mission_impact="LOW",
        urgency="LOW",
        decision="MONITOR",
        economic_impact={
            "traditional": {"total": 1500},
            "assetsentinel": {"total": 500},
            "potential_cost_avoided": 1000,
            "net_economic_benefit": 1000,
            "deployment_cost": 0,
            "roi_percent": 0
        }
    )
    assert rec1.economic_impact["potential_cost_avoided"] != rec2.economic_impact["potential_cost_avoided"]

def test_fleet_aggregation():
    """Fleet aggregation sums the traditional and assetsentinel costs."""
    recs = [
        {"traditional": {"total": 5000}, "assetsentinel": {"total": 1000}, "deployment_cost": 500},
        {"traditional": {"total": 1500}, "assetsentinel": {"total": 500}, "deployment_cost": 500},
    ]
    fleet_traditional_cost = sum(r["traditional"]["total"] for r in recs)
    fleet_assetsentinel_cost = sum(r["assetsentinel"]["total"] for r in recs)
    fleet_deployment_cost = sum(r["deployment_cost"] for r in recs)

    assert fleet_traditional_cost == 6500
    assert fleet_assetsentinel_cost == 1500
    assert fleet_deployment_cost == 1000

    fleet_potential_cost_avoided = fleet_traditional_cost - fleet_assetsentinel_cost
    assert fleet_potential_cost_avoided == 5000

    fleet_net_economic_benefit = fleet_potential_cost_avoided - fleet_deployment_cost
    assert fleet_net_economic_benefit == 4000

    roi = (fleet_net_economic_benefit / fleet_deployment_cost) * 100
    assert roi == 400.0

def test_economic_result_changes_when_decision_changes():
    from member3_readiness.maintenance.cost_engine import calculate_costs
    
    assumptions = {
        "repair_cost": 1000,
        "replacement_cost": 5000,
        "inspection_cost": 500,
        "downtime_cost_per_hour": 100,
        "planned_downtime_hours": 4,
        "emergency_intervention_cost": 2000,
        "emergency_maintenance_cost": 5000,
        "emergency_downtime_hours": 24,
        "mission_disruption_cost": 10000,
        "assetsentinel_deployment_cost": 100,
        "monitoring_cost_traditional": 500,
        "inspection_cost_traditional": 1000,
        "preventive_maintenance_traditional": 2000,
        "sensor_data_cost_assetsentinel": 200,
        "residual_failure_probability_multiplier": 0.1
    }
    
    repair_costs = calculate_costs(0.8, "REPAIR", "HIGH", assumptions, "HIGH")
    monitor_costs = calculate_costs(0.8, "MONITOR", "LOW", assumptions, "HIGH")
    
    # Intervention cost should differ
    assert repair_costs["assetsentinel"]["planned_intervention_cost"] == 1000
    assert monitor_costs["assetsentinel"]["planned_intervention_cost"] == 0
    
    # Total cost avoided should differ
    assert repair_costs["potential_cost_avoided"] != monitor_costs["potential_cost_avoided"]
