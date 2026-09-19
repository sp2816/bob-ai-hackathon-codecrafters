"""
AssetSentinel — Decision Engine
Member 3 (Tisha) | src/backend/member3_readiness/maintenance/decision_engine.py

Determines the deterministic Repair vs Replace decision.
"""
from typing import Dict, Any, Tuple
from member3_readiness.evidence.models import EvidenceObject
from member3_readiness.maintenance.cost_engine import calculate_costs

def evaluate_decision(
    evidence: EvidenceObject,
    cost_assumptions: Dict[str, float],
    urgency_level: str
) -> Tuple[str, Dict[str, Any]]:
    """
    Rules:
    - MONITOR: Low risk, no high anomaly, COMPLETED maintenance.
    - INSPECT_FIRST: Missing assumptions, SCHEDULED, conflicting signals.
    - REPAIR: Medium/High risk, repair < replacement cost.
    - REPLACE: Severe anomaly, high risk, or replacement < repair cost.
    
    Returns: (decision, cost_details)
    """
    risk = evidence.risk_level
    anomaly = evidence.anomaly.severity
    inspection_status = evidence.maintenance.inspection_status
    failure_prob = evidence.failure_risk
    
    repair_cost = cost_assumptions.get("repair_cost", 0.0)
    replacement_cost = cost_assumptions.get("replacement_cost", 0.0)
    inspection_cost = cost_assumptions.get("inspection_cost", 0.0)
    
    if repair_cost == 0.0 or replacement_cost == 0.0 or inspection_cost == 0.0:
        decision = "INSPECT_FIRST"
    elif risk == "LOW" and anomaly != "HIGH" and inspection_status == "COMPLETED":
        decision = "MONITOR"
    elif anomaly == "HIGH" or replacement_cost < repair_cost:
        decision = "REPLACE"
    elif risk in ["MEDIUM", "HIGH"] and repair_cost > 0:
        decision = "REPAIR"
    else:
        decision = "INSPECT_FIRST"
        
    economic_impact = calculate_costs(
        failure_prob, 
        decision,
        urgency_level,
        cost_assumptions, 
        evidence.mission_impact
    )
    
    return decision, economic_impact
