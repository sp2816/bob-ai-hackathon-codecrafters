"""
AssetSentinel — Timeline Engine
Member 3 (Tisha) | src/backend/member3_readiness/maintenance/timeline_engine.py

Generates deterministic dynamic timelines on-the-fly.
"""
from typing import List, Dict, Any
from member3_readiness.evidence.models import EvidenceObject

def build_timeline(
    evidence: EvidenceObject,
    decision: str,
    urgency: str
) -> List[Dict[str, Any]]:
    timeline = []
    
    # Standard timings mapping
    timing_str = "MONITOR"
    if urgency == "HIGH":
        timing_str = "IMMEDIATE"
    elif urgency == "MEDIUM":
        timing_str = "WITHIN_7_DAYS"
    elif urgency == "LOW" and decision != "MONITOR":
        timing_str = "NEXT_SCHEDULED_MAINTENANCE"
    
    # 1. Action Step
    if urgency == "HIGH":
        timeline.append({"action": f"Immediate {decision.lower()} required", "urgency": "IMMEDIATE", "time": timing_str, "reason": "Component critical or overdue"})
    elif urgency == "MEDIUM":
        timeline.append({"action": f"Schedule {decision.lower()}", "urgency": "PLANNED", "time": timing_str, "reason": "Elevated risk"})
    else:
        timeline.append({"action": "Routine monitoring", "urgency": "ROUTINE", "time": timing_str, "reason": "Low risk"})
        
    # 2. Next Action
    if decision in ["REPAIR", "REPLACE"]:
        timeline.append({"action": f"Execute {decision.lower()} protocol", "urgency": "PLANNED", "time": "PLANNED_WINDOW", "reason": "Based on economic impact analysis"})
    
    # 3. Post-Maintenance
    if decision != "MONITOR":
        timeline.append({"action": "Re-run prediction model", "urgency": "ROUTINE", "time": "POST_MAINTENANCE", "reason": "Verify component health"})
        timeline.append({"action": "Recalculate mission readiness", "urgency": "ROUTINE", "time": "POST_MAINTENANCE", "reason": "Clear conditionally ready status"})

    return timeline
