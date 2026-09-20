import pytest
from member3_readiness.evidence.models import EvidenceObject
from member3_readiness.maintenance.cost_engine import calculate_costs
from member3_readiness.maintenance.decision_engine import evaluate_decision
from member3_readiness.maintenance.timeline_engine import build_timeline

@pytest.fixture
def dummy_evidence():
    return EvidenceObject(
        asset_id="AS-TEST",
        component="engine",
        failure_risk=0.85,
        risk_level="HIGH",
        anomaly={"sensor": "vibration", "severity": "HIGH"},
        maintenance={"hours_since_service": 500, "inspection_status": "OVERDUE"},
        criticality="HIGH",
        mission_impact="HIGH"
    )

def test_cost_engine():
    failure_prob = 0.85
    assumptions = {
        "inspection_cost": 500,
        "repair_cost": 2000,
        "replacement_cost": 10000,
        "failure_impact_cost": 50000,
        "emergency_intervention_cost": 15000,
        "emergency_maintenance_cost": 25000,
        "downtime_cost_per_hour": 1000,
        "planned_downtime_hours": 10,
        "emergency_downtime_hours": 48,
        "mission_disruption_cost": 100000
    }
    costs = calculate_costs(failure_prob, "REPAIR", assumptions, "HIGH")
    
    # failure_scenario_cost = 15000 + 25000 + (48 * 1000) + 100000 = 188000
    # expected_failure_cost = 0.85 * 188000 = 159800
    # total_modeled_cost = 2000 + (10 * 1000) = 12000
    # potential_cost_avoided = 159800 - 12000 = 147800
    
    assert costs["without_assetsentinel"]["expected_failure_cost"] == 159800
    assert costs["with_assetsentinel"]["total_modeled_cost"] == 12000
    assert costs["potential_cost_avoided"] == 147800

def test_decision_engine(dummy_evidence):
    assumptions = {
        "inspection_cost": 500,
        "repair_cost": 2000,
        "replacement_cost": 10000,
        "failure_impact_cost": 50000,
        "emergency_intervention_cost": 15000,
        "emergency_maintenance_cost": 25000,
        "downtime_cost_per_hour": 1000,
        "planned_downtime_hours": 10,
        "emergency_downtime_hours": 48,
        "mission_disruption_cost": 100000
    }
    decision, costs = evaluate_decision(dummy_evidence, assumptions)
    assert decision == "REPLACE" # Because failure_risk >= 0.8 and severity == HIGH
    
    # failure_scenario_cost = 188000
    # expected_failure_cost = 0.85 * 188000 = 159800
    # total_modeled_cost = 10000 (replacement) + (10 * 1000) = 20000
    # potential_cost_avoided = 159800 - 20000 = 139800
    
    assert costs["with_assetsentinel"]["total_modeled_cost"] == 20000
    assert costs["potential_cost_avoided"] == 139800

def test_timeline_engine():
    timeline = build_timeline(None, "REPAIR", "HIGH")
    assert len(timeline) > 0
    assert "repair" in timeline[0]["action"].lower() or "repair" in timeline[1]["action"].lower()

    timeline = build_timeline(None, "MONITOR", "LOW")
    assert len(timeline) > 0
    assert "check" in timeline[0]["action"].lower() or "monitor" in timeline[0]["action"].lower()
