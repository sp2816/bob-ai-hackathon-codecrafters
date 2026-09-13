"""
AssetSentinel — Maintenance Priority Engine Tests
Member 3 (Tisha) | src/backend/member3_readiness/tests/test_maintenance.py

Tests for:
    - maintenance/models.py (MaintenanceRecommendation)
    - maintenance/priority_engine.py (rank_maintenance, score formula, helpers)

Test strategy:
    - All inputs are deterministic.
    - Verifies that the priority score formula drives ranking — NOT raw failure_risk.
    - Verifies contract §17: do NOT hardcode AS-1047 as rank 1; ranking emerges
      from the actual priority calculation.
    - Uses AS-1047 canonical scenario to show it DOES rank first when the
      formula produces the highest score.

Coverage targets:
    - MaintenanceRecommendation model validation
    - Priority score formula arithmetic
    - Urgency mapping (OVERDUE→HIGH, SCHEDULED→MEDIUM, COMPLETED→LOW)
    - Action and reason text generation
    - Ranking order (highest priority_score → rank 1)
    - Fleet-wide multi-asset, multi-component ranking
    - component_id_map resolves component IDs correctly
    - Empty evidence list raises ValueError
    - AS-1047 bearing ranks #1 in fleet scenario (formula-derived, not hardcoded)
    - Equal-score tie handling (deterministic — both included)
"""

from __future__ import annotations

import pytest

from member3_readiness.evidence.builder import build_evidence
from member3_readiness.evidence.models import AnomalyEvidence, EvidenceObject, MaintenanceEvidence
from member3_readiness.maintenance.models import MaintenanceRecommendation
from member3_readiness.maintenance.priority_engine import (
    _build_action,
    _build_reason,
    _compute_priority_score,
    _get_urgency_level,
    _get_urgency_score,
    rank_maintenance,
)
from member3_readiness.config.settings import MAINTENANCE_CONFIG, MAINTENANCE_STATUS_TO_URGENCY


# ===========================================================================
# Helper factory
# ===========================================================================

def _make_evidence(
    asset_id: str = "AS-0001",
    component: str = "engine",
    failure_risk: float = 0.30,
    risk_level: str = "LOW",
    anomaly_severity: str = "LOW",
    criticality: str = "LOW",
    maintenance_status: str = "COMPLETED",
    hours: float = 100.0,
    mission_impact: str = "NONE",
) -> EvidenceObject:
    return EvidenceObject(
        asset_id=asset_id,
        component=component,
        failure_risk=failure_risk,
        risk_level=risk_level,
        anomaly=AnomalyEvidence(sensor="vibration", severity=anomaly_severity),
        maintenance=MaintenanceEvidence(
            hours_since_service=hours, inspection_status=maintenance_status
        ),
        criticality=criticality,
        mission_impact=mission_impact,
    )


# ===========================================================================
# MaintenanceRecommendation model tests
# ===========================================================================

class TestMaintenanceRecommendationModel:
    def test_valid_construction(self):
        rec = MaintenanceRecommendation(
            recommendation_id="REC-001",
            asset_id="AS-1047",
            component_id="BRG-1047",
            component="main_bearing",
            priority=1,
            priority_score=0.85,
            action="Inspect and replace bearing",
            reason="High failure risk",
            risk="HIGH",
            mission_impact="HIGH",
            urgency="HIGH",
        )
        assert rec.priority == 1
        assert rec.status == "OPEN"  # default

    def test_priority_must_be_positive(self):
        with pytest.raises(Exception):
            MaintenanceRecommendation(
                recommendation_id="REC-X",
                asset_id="AS-1047",
                component_id="BRG-1047",
                component="main_bearing",
                priority=0,   # invalid — must be >= 1
                priority_score=0.85,
                action="action",
                reason="reason",
                risk="HIGH",
                mission_impact="HIGH",
                urgency="HIGH",
            )

    def test_priority_score_out_of_range_raises(self):
        with pytest.raises(Exception):
            MaintenanceRecommendation(
                recommendation_id="REC-X",
                asset_id="AS-1047",
                component_id="BRG-1047",
                component="main_bearing",
                priority=1,
                priority_score=1.5,   # > 1.0
                action="action",
                reason="reason",
                risk="HIGH",
                mission_impact="HIGH",
                urgency="HIGH",
            )

    def test_invalid_status_raises(self):
        with pytest.raises(Exception):
            MaintenanceRecommendation(
                recommendation_id="REC-X",
                asset_id="AS-1047",
                component_id="BRG-1047",
                component="main_bearing",
                priority=1,
                priority_score=0.85,
                action="action",
                reason="reason",
                risk="HIGH",
                mission_impact="HIGH",
                urgency="HIGH",
                status="DONE",  # type: ignore[arg-type]  # invalid
            )


# ===========================================================================
# Urgency helpers tests
# ===========================================================================

class TestUrgencyHelpers:
    def test_overdue_urgency_score_is_one(self):
        assert _get_urgency_score("OVERDUE") == 1.0

    def test_scheduled_urgency_score(self):
        assert _get_urgency_score("SCHEDULED") == 0.4

    def test_completed_urgency_score_is_zero(self):
        assert _get_urgency_score("COMPLETED") == 0.0

    def test_overdue_urgency_level_is_high(self):
        assert _get_urgency_level("OVERDUE") == "HIGH"

    def test_scheduled_urgency_level_is_medium(self):
        assert _get_urgency_level("SCHEDULED") == "MEDIUM"

    def test_completed_urgency_level_is_low(self):
        assert _get_urgency_level("COMPLETED") == "LOW"

    def test_maintenance_status_to_urgency_config_alignment(self):
        """MAINTENANCE_STATUS_TO_URGENCY in settings must match urgency helper."""
        assert MAINTENANCE_STATUS_TO_URGENCY["OVERDUE"] == _get_urgency_score("OVERDUE")
        assert MAINTENANCE_STATUS_TO_URGENCY["SCHEDULED"] == _get_urgency_score("SCHEDULED")
        assert MAINTENANCE_STATUS_TO_URGENCY["COMPLETED"] == _get_urgency_score("COMPLETED")


# ===========================================================================
# Priority score formula tests
# ===========================================================================

class TestComputePriorityScore:
    def test_all_high_inputs_produce_high_score(self):
        ev = _make_evidence(
            failure_risk=1.0, risk_level="HIGH", criticality="HIGH",
            maintenance_status="OVERDUE", mission_impact="HIGH"
        )
        score = _compute_priority_score(ev)
        assert abs(score - 1.0) < 1e-9

    def test_all_low_inputs_produce_low_score(self):
        ev = _make_evidence(
            failure_risk=0.0, risk_level="LOW", criticality="LOW",
            maintenance_status="COMPLETED", mission_impact="NONE"
        )
        score = _compute_priority_score(ev)
        w = MAINTENANCE_CONFIG.weights
        # 0.40×0.0 + 0.25×0.25 + 0.20×0.0 + 0.15×0.0 = 0.0625
        expected = w.failure_risk * 0.0 + w.criticality * 0.25 + w.mission_impact * 0.0 + w.urgency * 0.0
        assert abs(score - expected) < 1e-9

    def test_as1047_canonical_priority_score(self):
        """
        AS-1047 bearing:
            failure_risk=0.87, HIGH criticality, OVERDUE, HIGH mission_impact.
        score = 0.40×0.87 + 0.25×1.0 + 0.20×1.0 + 0.15×1.0 = 0.348+0.25+0.20+0.15 = 0.948
        """
        ev = _make_evidence(
            asset_id="AS-1047", component="main_bearing",
            failure_risk=0.87, risk_level="HIGH", criticality="HIGH",
            maintenance_status="OVERDUE", mission_impact="HIGH"
        )
        score = _compute_priority_score(ev)
        w = MAINTENANCE_CONFIG.weights
        expected = (
            w.failure_risk * 0.87
            + w.criticality * 1.0
            + w.mission_impact * 1.0
            + w.urgency * 1.0
        )
        assert abs(score - expected) < 1e-9

    def test_higher_urgency_score_beats_higher_failure_risk_alone(self):
        """
        Component A: failure_risk=0.90, LOW criticality, COMPLETED, NONE mission_impact
        Component B: failure_risk=0.50, HIGH criticality, OVERDUE, HIGH mission_impact

        A score = 0.40×0.90 + 0.25×0.25 + 0.20×0.0 + 0.15×0.0 = 0.36 + 0.0625 = 0.4225
        B score = 0.40×0.50 + 0.25×1.0 + 0.20×1.0 + 0.15×1.0  = 0.20 + 0.25 + 0.20 + 0.15 = 0.80

        B should rank higher than A — proving we do NOT just sort by failure_risk.
        """
        ev_a = _make_evidence(
            failure_risk=0.90, criticality="LOW", maintenance_status="COMPLETED", mission_impact="NONE"
        )
        ev_b = _make_evidence(
            failure_risk=0.50, criticality="HIGH", maintenance_status="OVERDUE", mission_impact="HIGH"
        )
        score_a = _compute_priority_score(ev_a)
        score_b = _compute_priority_score(ev_b)
        assert score_b > score_a  # multi-factor ranking, not just failure_risk


# ===========================================================================
# rank_maintenance() integration tests
# ===========================================================================

class TestRankMaintenance:
    def test_empty_list_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            rank_maintenance([])

    def test_single_component_gets_rank_1(self):
        ev = _make_evidence()
        result = rank_maintenance([ev])
        assert len(result) == 1
        assert result[0].priority == 1

    def test_returns_maintenance_recommendation_instances(self):
        ev = _make_evidence()
        result = rank_maintenance([ev])
        assert isinstance(result[0], MaintenanceRecommendation)

    def test_result_count_matches_input_count(self):
        evs = [_make_evidence(asset_id=f"AS-{i:04d}") for i in range(5)]
        result = rank_maintenance(evs)
        assert len(result) == 5

    def test_ranks_are_sequential_from_1(self):
        evs = [_make_evidence(asset_id=f"AS-{i:04d}", failure_risk=0.1 * i) for i in range(1, 4)]
        result = rank_maintenance(evs)
        assert [r.priority for r in result] == [1, 2, 3]

    def test_sorted_descending_by_priority_score(self):
        ev_low = _make_evidence(failure_risk=0.10, criticality="LOW")
        ev_mid = _make_evidence(failure_risk=0.50, criticality="MEDIUM")
        ev_high = _make_evidence(failure_risk=0.87, criticality="HIGH", maintenance_status="OVERDUE")
        result = rank_maintenance([ev_low, ev_mid, ev_high])
        scores = [r.priority_score for r in result]
        assert scores == sorted(scores, reverse=True)

    def test_rank_1_has_highest_score(self):
        ev_low = _make_evidence(failure_risk=0.10, criticality="LOW")
        ev_high = _make_evidence(failure_risk=0.87, criticality="HIGH", maintenance_status="OVERDUE",
                                 mission_impact="HIGH")
        result = rank_maintenance([ev_low, ev_high])
        assert result[0].priority == 1
        assert result[0].priority_score > result[1].priority_score

    def test_component_id_map_applied(self):
        ev = _make_evidence(asset_id="AS-1047", component="main_bearing")
        cid_map = {("AS-1047", "main_bearing"): "BRG-1047"}
        result = rank_maintenance([ev], component_id_map=cid_map)
        assert result[0].component_id == "BRG-1047"

    def test_missing_component_id_uses_placeholder(self):
        ev = _make_evidence(asset_id="AS-1047", component="main_bearing")
        result = rank_maintenance([ev], component_id_map=None)
        assert result[0].component_id == "AS-1047-main_bearing"

    def test_recommendation_has_action(self):
        ev = _make_evidence()
        result = rank_maintenance([ev])
        assert len(result[0].action) > 0

    def test_recommendation_has_reason(self):
        ev = _make_evidence()
        result = rank_maintenance([ev])
        assert len(result[0].reason) > 0

    def test_recommendation_has_asset_id(self):
        ev = _make_evidence(asset_id="AS-1047")
        result = rank_maintenance([ev])
        assert result[0].asset_id == "AS-1047"

    def test_recommendation_has_component(self):
        ev = _make_evidence(component="main_bearing")
        result = rank_maintenance([ev])
        assert result[0].component == "main_bearing"

    def test_overdue_gets_high_urgency(self):
        ev = _make_evidence(maintenance_status="OVERDUE")
        result = rank_maintenance([ev])
        assert result[0].urgency == "HIGH"

    def test_scheduled_gets_medium_urgency(self):
        ev = _make_evidence(maintenance_status="SCHEDULED")
        result = rank_maintenance([ev])
        assert result[0].urgency == "MEDIUM"

    def test_completed_gets_low_urgency(self):
        ev = _make_evidence(maintenance_status="COMPLETED")
        result = rank_maintenance([ev])
        assert result[0].urgency == "LOW"


# ===========================================================================
# Action text generation tests
# ===========================================================================

class TestBuildAction:
    def test_overdue_action_mentions_overdue(self):
        ev = _make_evidence(maintenance_status="OVERDUE")
        action = _build_action(ev)
        assert "overdue" in action.lower() or "immediate" in action.lower()

    def test_high_risk_action_mentions_replace(self):
        ev = _make_evidence(risk_level="HIGH", maintenance_status="COMPLETED")
        action = _build_action(ev)
        assert "inspect" in action.lower() or "replace" in action.lower()

    def test_medium_risk_action_mentions_assess(self):
        ev = _make_evidence(risk_level="MEDIUM", maintenance_status="COMPLETED")
        action = _build_action(ev)
        assert "inspect" in action.lower() or "assess" in action.lower()

    def test_low_risk_action_mentions_schedule(self):
        ev = _make_evidence(risk_level="LOW", maintenance_status="COMPLETED")
        action = _build_action(ev)
        assert "schedule" in action.lower() or "routine" in action.lower()


# ===========================================================================
# Fleet-wide multi-asset ranking (canonical scenario)
# ===========================================================================

class TestFleetRanking:
    """
    Fleet scenario testing that the priority formula drives rankings correctly.
    AS-1047 bearing must rank #1 based on its scores — not because it's hardcoded.
    """

    @pytest.fixture
    def fleet_evidence(self, as1047_prediction, as1047_component_info, as1047_maintenance_overdue):
        """Fleet of 4 components from 3 assets."""
        # AS-1047 main_bearing: HIGH risk, OVERDUE, HIGH crit, HIGH mission_impact
        ev_1047_bearing = build_evidence(
            prediction=as1047_prediction,
            component_info=as1047_component_info,
            maintenance_info=as1047_maintenance_overdue,
            mission_impact="HIGH",
        )
        # AS-1001 main_bearing: LOW risk, COMPLETED, HIGH crit, NONE impact
        from member3_readiness.evidence.models import ComponentInfo, MaintenanceInfo
        from datetime import datetime, timezone
        healthy_comp = ComponentInfo(
            component_id="BRG-1001", asset_id="AS-1001",
            component_type="main_bearing", criticality="HIGH"
        )
        healthy_maint = MaintenanceInfo(
            maintenance_id="MNT-0007", asset_id="AS-1001",
            component_id="BRG-1001", maintenance_type="INSPECTION",
            maintenance_date=datetime(2026, 1, 16, tzinfo=timezone.utc),
            status="COMPLETED", hours_since_service=120.0,
        )
        from member2_ml.services.prediction_service import ComponentPredictionResult  # noqa: E402
        from .conftest import FIXED_TIMESTAMP
        healthy_pred = ComponentPredictionResult(
            prediction_id="PRED-BRG1001",
            asset_id="AS-1001", component_id="BRG-1001",
            failure_probability=0.08, risk_category="LOW",
            anomaly_score=0.15, anomaly_status="NORMAL", anomaly_severity="LOW",
            sensor="NONE", timestamp=FIXED_TIMESTAMP,
        )
        ev_1001_bearing = build_evidence(
            prediction=healthy_pred, component_info=healthy_comp,
            maintenance_info=healthy_maint, mission_impact="NONE",
        )
        # AS-1002 engine: MEDIUM risk, SCHEDULED, MEDIUM crit, NONE impact
        ev_1002_engine = EvidenceObject(
            asset_id="AS-1002", component="engine",
            failure_risk=0.50, risk_level="MEDIUM",
            anomaly=AnomalyEvidence(sensor="temperature", severity="MEDIUM"),
            maintenance=MaintenanceEvidence(
                hours_since_service=80.0, inspection_status="SCHEDULED"
            ),
            criticality="MEDIUM", mission_impact="NONE",
        )
        # AS-1003 hydraulics: LOW risk, COMPLETED, LOW crit, NONE impact
        ev_1003_hydraulics = EvidenceObject(
            asset_id="AS-1003", component="hydraulics",
            failure_risk=0.15, risk_level="LOW",
            anomaly=AnomalyEvidence(sensor="pressure", severity="LOW"),
            maintenance=MaintenanceEvidence(
                hours_since_service=30.0, inspection_status="COMPLETED"
            ),
            criticality="LOW", mission_impact="NONE",
        )
        return [ev_1047_bearing, ev_1001_bearing, ev_1002_engine, ev_1003_hydraulics]

    def test_as1047_bearing_ranks_first(self, fleet_evidence):
        """
        AS-1047 bearing has the highest priority score in the fleet.
        Rank 1 emerges from formula — not hardcoded.
        """
        result = rank_maintenance(fleet_evidence)
        assert result[0].asset_id == "AS-1047"
        assert result[0].component == "main_bearing"
        assert result[0].priority == 1

    def test_fleet_result_count_is_four(self, fleet_evidence):
        result = rank_maintenance(fleet_evidence)
        assert len(result) == 4

    def test_fleet_ranks_sequential(self, fleet_evidence):
        result = rank_maintenance(fleet_evidence)
        assert [r.priority for r in result] == [1, 2, 3, 4]

    def test_fleet_scores_descending(self, fleet_evidence):
        result = rank_maintenance(fleet_evidence)
        scores = [r.priority_score for r in result]
        assert scores == sorted(scores, reverse=True)

    def test_as1047_recommendation_id_format(self, fleet_evidence):
        result = rank_maintenance(fleet_evidence)
        rec_1047 = next(r for r in result if r.asset_id == "AS-1047")
        assert rec_1047.recommendation_id.startswith("REC-001")

    def test_as1047_recommendation_has_overdue_mention(self, fleet_evidence):
        result = rank_maintenance(fleet_evidence)
        rec_1047 = next(r for r in result if r.asset_id == "AS-1047")
        assert "overdue" in rec_1047.action.lower() or "immediate" in rec_1047.action.lower()

    def test_healthy_asset_ranks_last(self, fleet_evidence):
        """AS-1003 (LOW everything) should be near the bottom."""
        result = rank_maintenance(fleet_evidence)
        last = result[-1]
        assert last.asset_id == "AS-1003"
