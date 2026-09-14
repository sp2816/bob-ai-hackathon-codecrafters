"""
AssetSentinel — Mission Evaluator
Member 3 (Tisha) | src/backend/member3_readiness/missions/evaluator.py
"""

from __future__ import annotations

from member3_readiness.evidence.models import EvidenceObject
from member3_readiness.missions.models import MissionInfo
from member3_readiness.readiness.engine import evaluate
from member3_readiness.readiness.models import ReadinessResult


def evaluate_for_mission(
    evidence_list: list[EvidenceObject], mission: MissionInfo
) -> ReadinessResult:
    """
    Evaluates asset readiness in the context of a specific mission.
    
    This function:
      1. Clones the evidence list.
      2. Maps mission impact onto components required by the mission.
      3. Forwards the updated evidence to the Readiness Engine.
      
    It does NOT implement readiness rules itself.
    """
    if not evidence_list:
        raise ValueError("evidence_list cannot be empty.")

    # Check if ANY component in the evidence list is explicitly required by the mission
    has_required_component = any(
        ev.component in mission.required_components for ev in evidence_list
    )

    mission_evidence = []
    for ev in evidence_list:
        # Create a copy so we don't mutate the generic evidence cache
        ev_copy = ev.model_copy()

        # Contract §12: The mission-specific impact is derived from
        # mission.required_components and mission.criticality.
        # Fallback: if an asset has NO components that match the explicit
        # required_components, we apply the mission criticality universally
        # to ensure the asset still receives a mission-specific evaluation.
        if has_required_component:
            if ev_copy.component in mission.required_components:
                ev_copy.mission_impact = mission.criticality
            else:
                ev_copy.mission_impact = "NONE"
        else:
            ev_copy.mission_impact = mission.criticality

        mission_evidence.append(ev_copy)

    # Note: Hard Rule 3 ("Mission-required component unavailable/non-functional")
    # is intentionally omitted because the contract lacks an explicit representation
    # of "unavailable/non-functional" state in EvidenceObject. 
    # (Reported as a contract gap).

    return evaluate(
        evidence_list=mission_evidence,
        mission_id=mission.mission_id,
        mission_threshold=mission.readiness_threshold,
    )
