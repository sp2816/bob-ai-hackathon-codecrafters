"""
AssetSentinel — Mission Tests
Member 3 (Tisha) | src/backend/member3_readiness/tests/test_missions.py
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from member3_readiness.evidence.models import AnomalyEvidence, EvidenceObject, MaintenanceEvidence
from member3_readiness.missions.models import MissionInfo
from member3_readiness.missions.evaluator import evaluate_for_mission
from member3_readiness.readiness.models import ReadinessResult


# ===========================================================================
# Helper factories
# ===========================================================================

def _make_evidence(
    component: str = "main_bearing",
    failure_risk: float = 0.30,
    criticality: str = "HIGH",
    maintenance_status: str = "COMPLETED",
) -> EvidenceObject:
    return EvidenceObject(
        asset_id="AS-1047",
        component=component,
        failure_risk=failure_risk,
        risk_level="LOW",
        anomaly=AnomalyEvidence(sensor="NONE", severity="LOW"),
        maintenance=MaintenanceEvidence(
            hours_since_service=100.0, inspection_status=maintenance_status
        ),
        criticality=criticality,
        mission_impact="NONE",
    )


def _make_mission(
    mission_id: str = "MSN-001",
    criticality: str = "MEDIUM",
    required_components: list[str] = None,
    readiness_threshold: float = None,
) -> MissionInfo:
    return MissionInfo(
        mission_id=mission_id,
        mission_name="Test Mission",
        mission_type="Patrol",
        criticality=criticality,
        scheduled_time=datetime.now(tz=timezone.utc),
        required_components=required_components or [],
        readiness_threshold=readiness_threshold,
    )


# ===========================================================================
# Model Tests
# ===========================================================================

class TestMissionModel:
    def test_accepts_valid_mission(self):
        m = _make_mission()
        assert m.mission_id == "MSN-001"
        assert m.criticality == "MEDIUM"

    def test_invalid_mission_enum_rejected(self):
        with pytest.raises(ValidationError):
            _make_mission(criticality="SUPER_HIGH")


# ===========================================================================
# Evaluator Logic Tests
# ===========================================================================

class TestEvaluatorLogic:
    def test_required_component_receives_impact(self):
        ev = _make_evidence(component="engine")
        m = _make_mission(criticality="HIGH", required_components=["engine"])
        
        result = evaluate_for_mission([ev], m)
        evaluated_ev = result.evidence[0]
        
        assert evaluated_ev.mission_impact == "HIGH"
        assert evaluated_ev.component == "engine"

    def test_non_required_component_receives_none_impact(self):
        ev = _make_evidence(component="hydraulics")
        m = _make_mission(criticality="HIGH", required_components=["engine"])
        
        result = evaluate_for_mission([ev], m)
        evaluated_ev = result.evidence[0]
        
        assert evaluated_ev.mission_impact == "NONE"

    def test_mission_with_multiple_required_components(self):
        ev1 = _make_evidence(component="engine")
        ev2 = _make_evidence(component="hydraulics")
        ev3 = _make_evidence(component="cabin_lights")
        m = _make_mission(criticality="MEDIUM", required_components=["engine", "hydraulics"])
        
        result = evaluate_for_mission([ev1, ev2, ev3], m)
        impacts = {e.component: e.mission_impact for e in result.evidence}
        
        assert impacts["engine"] == "MEDIUM"
        assert impacts["hydraulics"] == "MEDIUM"
        assert impacts["cabin_lights"] == "NONE"

    def test_mission_with_no_required_components(self):
        ev = _make_evidence(component="engine")
        m = _make_mission(criticality="HIGH", required_components=[])
        
        result = evaluate_for_mission([ev], m)
        assert result.evidence[0].mission_impact == "NONE"

    def test_mission_id_is_preserved_in_result(self):
        ev = _make_evidence()
        m = _make_mission(mission_id="MSN-XYZ")
        
        result = evaluate_for_mission([ev], m)
        assert result.mission_id == "MSN-XYZ"

    def test_same_evidence_different_mission_criticality(self):
        # A component that is required by two missions with different criticalities
        ev = _make_evidence(component="engine")
        
        m_low = _make_mission(criticality="LOW", required_components=["engine"])
        m_high = _make_mission(criticality="HIGH", required_components=["engine"])
        
        res_low = evaluate_for_mission([ev], m_low)
        res_high = evaluate_for_mission([ev], m_high)
        
        # High criticality mission should result in a higher risk score
        assert res_high.readiness_score > res_low.readiness_score

    def test_readiness_threshold_override(self):
        # Evidence that produces a score between 0.35 and 0.66 (normally CONDITIONALLY_READY)
        ev = _make_evidence(component="engine", failure_risk=0.5, criticality="HIGH")
        # Ensure it hits CONDITIONALLY_READY natively
        from member3_readiness.readiness.engine import evaluate
        normal_res = evaluate([ev])
        assert normal_res.readiness_status == "CONDITIONALLY_READY"
        
        # But if the mission has a strict threshold that is lower than the score
        strict_threshold = normal_res.readiness_score - 0.01
        m_strict = _make_mission(
            readiness_threshold=strict_threshold, 
            required_components=["engine"]
        )
        
        res_strict = evaluate_for_mission([ev], m_strict)
        assert res_strict.readiness_status == "NOT_READY"

    def test_generic_readiness_remains_unchanged(self):
        # The original evidence list should not be mutated
        ev = _make_evidence(component="engine")
        m = _make_mission(criticality="HIGH", required_components=["engine"])
        
        evaluate_for_mission([ev], m)
        assert ev.mission_impact == "NONE"

    def test_deterministic_output(self):
        ev = _make_evidence(component="engine")
        m = _make_mission(criticality="HIGH", required_components=["engine"])
        
        res1 = evaluate_for_mission([ev], m)
        res2 = evaluate_for_mission([ev], m)
        
        assert res1.readiness_score == res2.readiness_score
        assert res1.readiness_status == res2.readiness_status

    def test_different_missions_different_results(self):
        # Base evidence gives a medium score
        ev = _make_evidence(component="engine", failure_risk=0.6, criticality="MEDIUM")
        
        # Training mission (LOW criticality, requires engine)
        m_train = _make_mission(mission_id="MSN-001", criticality="LOW", required_components=["engine"])
        
        # Strike mission (HIGH criticality, requires engine)
        m_strike = _make_mission(mission_id="MSN-003", criticality="HIGH", required_components=["engine"])
        
        res_train = evaluate_for_mission([ev], m_train)
        res_strike = evaluate_for_mission([ev], m_strike)
        
        assert res_strike.readiness_score > res_train.readiness_score
        
    def test_no_member_2_import(self):
        # Ensure evaluator.py doesn't import member2_ml (no sys.path hacks needed)
        import pathlib
        evaluator_path = pathlib.Path(__file__).parent.parent / "missions" / "evaluator.py"
        content = evaluator_path.read_text(encoding="utf-8")
        assert "member2_ml" not in content
        assert "sys.path" not in content
