"""
AssetSentinel — Readiness Engine Tests
Member 3 (Tisha) | src/backend/member3_readiness/tests/test_readiness.py

Tests for:
    - config/settings.py  (weights, thresholds, normalization)
    - readiness/models.py (ReadinessResult)
    - readiness/engine.py (evaluate(), hard rules, weighted scoring)

Test strategy:
    - All inputs are deterministic fixtures from conftest.py.
    - No real ML inference is performed.
    - Tests verify the ENGINE logic, not the data — AS-1047 values are used
      because they match the contract §23 canonical scenario, not because
      we hardcode AS-1047 as a special case.

Coverage targets:
    - Config singleton validation
    - Normalization edge cases
    - Hard Rule 1: OVERDUE + HIGH criticality → NOT_READY
    - Hard Rule 2: failure_risk > threshold + HIGH criticality → NOT_READY
    - Hard rules do NOT fire for non-critical components
    - Hard rules do NOT fire when maintenance is COMPLETED / SCHEDULED
    - Hard rules do NOT fire when failure_risk is below threshold
    - Score formula correctness (exact arithmetic)
    - Threshold boundary conditions
    - Multi-component aggregation (max score strategy)
    - AS-1047 canonical demo scenario (contract §23)
    - Empty evidence list raises ValueError
    - Reasons list is non-empty for non-READY results
    - READY result returns positive confirmation reason
"""

from __future__ import annotations

import math
import pytest

from member3_readiness.config.settings import (
    LEVEL_TO_FLOAT,
    MAINTENANCE_CONFIG,
    READINESS_CONFIG,
    ReadinessWeights,
    ReadinessThresholds,
    HardRuleThresholds,
    MaintenanceWeights,
)
from member3_readiness.evidence.models import (
    AnomalyEvidence,
    ComponentInfo,
    EvidenceObject,
    MaintenanceEvidence,
    MaintenanceInfo,
)
from member3_readiness.readiness.engine import (
    _compute_component_score,
    _normalize,
    _score_to_status,
    evaluate,
)
from member3_readiness.readiness.models import ReadinessResult
from member3_readiness.evidence.builder import build_evidence


# ===========================================================================
# Config / Settings tests
# ===========================================================================

class TestReadinessWeights:
    def test_default_weights_sum_to_one(self):
        w = ReadinessWeights()
        total = w.failure_risk + w.anomaly_severity + w.criticality + w.mission_impact
        assert abs(total - 1.0) < 1e-9

    def test_default_values(self):
        w = ReadinessWeights()
        assert w.failure_risk == 0.40
        assert w.anomaly_severity == 0.25
        assert w.criticality == 0.20
        assert w.mission_impact == 0.15

    def test_invalid_weights_raise_value_error(self):
        with pytest.raises(ValueError, match="must sum to 1.0"):
            ReadinessWeights(failure_risk=0.50, anomaly_severity=0.25,
                             criticality=0.20, mission_impact=0.15)

    def test_frozen(self):
        w = ReadinessWeights()
        with pytest.raises((AttributeError, TypeError)):
            w.failure_risk = 0.99  # type: ignore[misc]


class TestReadinessThresholds:
    def test_default_values(self):
        t = ReadinessThresholds()
        assert t.ready_max == 0.34
        assert t.conditionally_ready_max == 0.66

    def test_inverted_thresholds_raise_value_error(self):
        with pytest.raises(ValueError, match="must satisfy"):
            ReadinessThresholds(ready_max=0.70, conditionally_ready_max=0.50)

    def test_zero_ready_max_raises(self):
        with pytest.raises(ValueError, match="must satisfy"):
            ReadinessThresholds(ready_max=0.0, conditionally_ready_max=0.66)


class TestHardRuleThresholds:
    def test_default_value(self):
        h = HardRuleThresholds()
        assert h.critical_failure_risk_hard_threshold == 0.75

    def test_zero_threshold_raises(self):
        with pytest.raises(ValueError, match="must be in"):
            HardRuleThresholds(critical_failure_risk_hard_threshold=0.0)


class TestMaintenanceWeights:
    def test_default_weights_sum_to_one(self):
        w = MaintenanceWeights()
        total = w.failure_risk + w.criticality + w.mission_impact + w.urgency
        assert abs(total - 1.0) < 1e-9

    def test_default_values(self):
        w = MaintenanceWeights()
        assert w.failure_risk == 0.40
        assert w.criticality == 0.25
        assert w.mission_impact == 0.20
        assert w.urgency == 0.15


class TestSingletons:
    def test_readiness_config_singleton_exists(self):
        assert READINESS_CONFIG is not None
        assert READINESS_CONFIG.weights is not None
        assert READINESS_CONFIG.thresholds is not None
        assert READINESS_CONFIG.hard_rules is not None

    def test_maintenance_config_singleton_exists(self):
        assert MAINTENANCE_CONFIG is not None
        assert MAINTENANCE_CONFIG.weights is not None

    def test_level_to_float_coverage(self):
        """All expected level keys are present and correctly mapped."""
        assert LEVEL_TO_FLOAT["NONE"] == 0.0
        assert LEVEL_TO_FLOAT["LOW"] == 0.25
        assert LEVEL_TO_FLOAT["MEDIUM"] == 0.60
        assert LEVEL_TO_FLOAT["HIGH"] == 1.0


# ===========================================================================
# Normalization helper tests
# ===========================================================================

class TestNormalize:
    def test_none_maps_to_zero(self):
        assert _normalize("NONE") == 0.0

    def test_low_maps_to_quarter(self):
        assert _normalize("LOW") == 0.25

    def test_medium_maps_to_point_six(self):
        assert _normalize("MEDIUM") == 0.60

    def test_high_maps_to_one(self):
        assert _normalize("HIGH") == 1.0

    def test_unknown_level_raises(self):
        with pytest.raises((ValueError, KeyError)):
            _normalize("EXTREME")


# ===========================================================================
# Score formula tests
# ===========================================================================

class TestScoreFormula:
    def _make_evidence(
        self,
        failure_risk: float = 0.5,
        anomaly_severity: str = "LOW",
        criticality: str = "LOW",
        mission_impact: str = "NONE",
    ) -> EvidenceObject:
        return EvidenceObject(
            asset_id="AS-TEST",
            component="test_component",
            failure_risk=failure_risk,
            risk_level="MEDIUM",
            anomaly=AnomalyEvidence(sensor="vibration", severity=anomaly_severity),
            maintenance=MaintenanceEvidence(
                hours_since_service=100.0, inspection_status="COMPLETED"
            ),
            criticality=criticality,
            mission_impact=mission_impact,
        )

    def test_all_zero_inputs_score(self):
        """failure_risk=0, NONE/NONE anomaly/mission, LOW criticality → near zero."""
        ev = self._make_evidence(
            failure_risk=0.0,
            anomaly_severity="LOW",
            criticality="LOW",
            mission_impact="NONE",
        )
        score = _compute_component_score(ev)
        w = READINESS_CONFIG.weights
        expected = (
            w.failure_risk * 0.0
            + w.anomaly_severity * 0.25   # LOW
            + w.criticality * 0.25        # LOW
            + w.mission_impact * 0.0      # NONE
        )
        assert abs(score - expected) < 1e-9

    def test_all_high_inputs_score_near_one(self):
        """All HIGH inputs → score near 1.0."""
        ev = self._make_evidence(
            failure_risk=1.0,
            anomaly_severity="HIGH",
            criticality="HIGH",
            mission_impact="HIGH",
        )
        score = _compute_component_score(ev)
        assert abs(score - 1.0) < 1e-9

    def test_as1047_canonical_score(self):
        """
        AS-1047 canonical scenario (contract §23):
            failure_risk=0.87, anomaly_severity=HIGH,
            criticality=HIGH, mission_impact=HIGH

        Expected score = 0.40×0.87 + 0.25×1.0 + 0.20×1.0 + 0.15×1.0 = 0.948
        """
        ev = self._make_evidence(
            failure_risk=0.87,
            anomaly_severity="HIGH",
            criticality="HIGH",
            mission_impact="HIGH",
        )
        score = _compute_component_score(ev)
        expected = 0.40 * 0.87 + 0.25 * 1.0 + 0.20 * 1.0 + 0.15 * 1.0
        assert abs(score - expected) < 1e-9

    def test_generic_evidence_uses_none_mission_impact(self):
        """For generic (non-mission) evidence, mission_impact='NONE' → 0 contribution."""
        ev = self._make_evidence(
            failure_risk=0.5,
            anomaly_severity="MEDIUM",
            criticality="MEDIUM",
            mission_impact="NONE",
        )
        score = _compute_component_score(ev)
        w = READINESS_CONFIG.weights
        expected = (
            w.failure_risk * 0.5
            + w.anomaly_severity * 0.60   # MEDIUM
            + w.criticality * 0.60        # MEDIUM
            + w.mission_impact * 0.0      # NONE
        )
        assert abs(score - expected) < 1e-9


# ===========================================================================
# Score-to-status mapping tests
# ===========================================================================

class TestScoreToStatus:
    def test_score_zero_is_ready(self):
        assert _score_to_status(0.0) == "READY"

    def test_score_at_ready_max_is_ready(self):
        assert _score_to_status(0.34) == "READY"

    def test_score_just_above_ready_max(self):
        assert _score_to_status(0.35) == "CONDITIONALLY_READY"

    def test_score_at_conditionally_ready_max(self):
        assert _score_to_status(0.66) == "CONDITIONALLY_READY"

    def test_score_just_above_conditionally_ready_max(self):
        assert _score_to_status(0.67) == "NOT_READY"

    def test_score_one_is_not_ready(self):
        assert _score_to_status(1.0) == "NOT_READY"

    def test_score_mid_conditionally_ready(self):
        assert _score_to_status(0.50) == "CONDITIONALLY_READY"


# ===========================================================================
# ReadinessResult model tests
# ===========================================================================

class TestReadinessResultModel:
    def test_valid_result_construction(self):
        result = ReadinessResult(
            asset_id="AS-0001",
            readiness_score=0.30,
            readiness_status="READY",
            reasons=["All components within acceptable readiness parameters."],
        )
        assert result.asset_id == "AS-0001"
        assert result.readiness_status == "READY"
        assert result.mission_id is None
        assert result.timestamp is not None

    def test_score_out_of_range_raises(self):
        with pytest.raises(Exception):
            ReadinessResult(
                asset_id="AS-0001",
                readiness_score=1.5,
                readiness_status="READY",
            )

    def test_invalid_status_raises(self):
        with pytest.raises(Exception):
            ReadinessResult(
                asset_id="AS-0001",
                readiness_score=0.5,
                readiness_status="UNKNOWN",  # type: ignore[arg-type]
            )


# ===========================================================================
# Hard Rule 1: Overdue inspection on critical component
# ===========================================================================

class TestHardRule1:
    def _make_overdue_critical_evidence(self, **overrides) -> EvidenceObject:
        return EvidenceObject(
            asset_id=overrides.get("asset_id", "AS-1047"),
            component=overrides.get("component", "main_bearing"),
            failure_risk=overrides.get("failure_risk", 0.30),   # LOW risk — rule 2 won't fire
            risk_level="LOW",
            anomaly=AnomalyEvidence(sensor="vibration", severity="HIGH"),
            maintenance=MaintenanceEvidence(
                hours_since_service=overrides.get("hours", 420.0),
                inspection_status=overrides.get("status", "OVERDUE"),
            ),
            criticality=overrides.get("criticality", "HIGH"),
            mission_impact="NONE",
        )

    def test_rule1_fires_overdue_high_criticality(self):
        """OVERDUE + HIGH criticality → NOT_READY regardless of score."""
        evidence = self._make_overdue_critical_evidence()
        result = evaluate([evidence])
        assert result.readiness_status == "NOT_READY"

    def test_rule1_reason_mentions_component_and_hours(self):
        evidence = self._make_overdue_critical_evidence(component="main_bearing", hours=420.0)
        result = evaluate([evidence])
        assert len(result.reasons) > 0
        reason = result.reasons[0].lower()
        assert "overdue" in reason or "inspection" in reason

    def test_rule1_does_not_fire_for_completed_maintenance(self):
        """COMPLETED maintenance — Rule 1 must NOT fire."""
        evidence = self._make_overdue_critical_evidence(status="COMPLETED")
        result = evaluate([evidence])
        # With failure_risk=0.30 and HIGH criticality (below threshold 0.75) →
        # score = 0.40×0.30 + 0.25×1.0 + 0.20×1.0 + 0.15×0.0 = 0.57 → CONDITIONALLY_READY
        assert result.readiness_status != "NOT_READY" or "overdue" not in result.reasons[0].lower()

    def test_rule1_does_not_fire_for_low_criticality(self):
        """LOW criticality — Rule 1 must NOT fire even if OVERDUE."""
        evidence = self._make_overdue_critical_evidence(criticality="LOW")
        result = evaluate([evidence])
        # Hard rule 1 only fires on HIGH criticality — LOW criticality is fine
        assert result.readiness_status in ("READY", "CONDITIONALLY_READY", "NOT_READY")
        # Verify reasons don't cite the hard-rule-1 text
        for reason in result.reasons:
            assert "mandatory inspection overdue on critical" not in reason.lower()

    def test_rule1_does_not_fire_for_scheduled_maintenance(self):
        """SCHEDULED maintenance — Rule 1 must NOT fire."""
        evidence = self._make_overdue_critical_evidence(status="SCHEDULED")
        result = evaluate([evidence])
        for reason in result.reasons:
            assert "mandatory inspection overdue on critical" not in reason.lower()


# ===========================================================================
# Hard Rule 2: Critical component failure_risk exceeds threshold
# ===========================================================================

class TestHardRule2:
    _THRESHOLD = 0.75  # must match config default

    def _make_high_risk_critical_evidence(self, **overrides) -> EvidenceObject:
        return EvidenceObject(
            asset_id=overrides.get("asset_id", "AS-1047"),
            component=overrides.get("component", "main_bearing"),
            failure_risk=overrides.get("failure_risk", 0.87),
            risk_level="HIGH",
            anomaly=AnomalyEvidence(
                sensor="vibration",
                severity=overrides.get("anomaly_severity", "HIGH"),
            ),
            maintenance=MaintenanceEvidence(
                hours_since_service=overrides.get("hours", 200.0),
                inspection_status=overrides.get("status", "SCHEDULED"),
            ),
            criticality=overrides.get("criticality", "HIGH"),
            mission_impact="NONE",
        )

    def test_rule2_fires_critical_high_failure_risk(self):
        """failure_risk > 0.75 + HIGH criticality → NOT_READY."""
        evidence = self._make_high_risk_critical_evidence(failure_risk=0.87, status="SCHEDULED")
        result = evaluate([evidence])
        assert result.readiness_status == "NOT_READY"

    def test_rule2_fires_at_threshold_boundary(self):
        """Exactly at 0.76 (above 0.75 threshold) → NOT_READY."""
        evidence = self._make_high_risk_critical_evidence(failure_risk=0.76, status="COMPLETED")
        result = evaluate([evidence])
        assert result.readiness_status == "NOT_READY"

    def test_rule2_does_not_fire_exactly_at_threshold(self):
        """Exactly at 0.75 — threshold is exclusive (> not >=)."""
        evidence = self._make_high_risk_critical_evidence(failure_risk=0.75, status="COMPLETED")
        result = evaluate([evidence])
        # Rule 2 uses strict > so 0.75 should NOT trigger it
        # (score-based path takes over)
        assert result.readiness_status in ("READY", "CONDITIONALLY_READY", "NOT_READY")
        for reason in result.reasons:
            assert "exceeds the configured threshold" not in reason

    def test_rule2_does_not_fire_for_low_criticality(self):
        """Even high failure_risk on LOW criticality → rule 2 must NOT fire."""
        evidence = self._make_high_risk_critical_evidence(
            failure_risk=0.99, criticality="LOW", status="COMPLETED"
        )
        result = evaluate([evidence])
        for reason in result.reasons:
            assert "exceeds the configured threshold" not in reason

    def test_rule2_does_not_fire_below_threshold(self):
        """failure_risk=0.60 (below 0.75) + HIGH criticality → no rule 2."""
        evidence = self._make_high_risk_critical_evidence(failure_risk=0.60, status="COMPLETED")
        result = evaluate([evidence])
        for reason in result.reasons:
            assert "exceeds the configured threshold" not in reason


# ===========================================================================
# evaluate() integration tests
# ===========================================================================

class TestEvaluate:
    def test_empty_evidence_list_raises(self):
        with pytest.raises(ValueError, match="at least one EvidenceObject"):
            evaluate([])

    def test_single_healthy_component_is_ready(self):
        evidence = EvidenceObject(
            asset_id="AS-0001",
            component="engine",
            failure_risk=0.05,
            risk_level="LOW",
            anomaly=AnomalyEvidence(sensor="NONE", severity="LOW"),
            maintenance=MaintenanceEvidence(
                hours_since_service=50.0, inspection_status="COMPLETED"
            ),
            criticality="LOW",
            mission_impact="NONE",
        )
        result = evaluate([evidence])
        assert result.readiness_status == "READY"
        assert result.readiness_score <= 0.34
        assert result.asset_id == "AS-0001"
        assert result.mission_id is None

    def test_medium_risk_is_conditionally_ready(self):
        evidence = EvidenceObject(
            asset_id="AS-0002",
            component="engine",
            failure_risk=0.50,
            risk_level="MEDIUM",
            anomaly=AnomalyEvidence(sensor="temperature", severity="MEDIUM"),
            maintenance=MaintenanceEvidence(
                hours_since_service=80.0, inspection_status="SCHEDULED"
            ),
            criticality="LOW",
            mission_impact="NONE",
        )
        result = evaluate([evidence])
        # score = 0.40×0.50 + 0.25×0.60 + 0.20×0.25 + 0.15×0.0 = 0.20+0.15+0.05+0.0 = 0.40
        assert result.readiness_status == "CONDITIONALLY_READY"
        assert 0.34 < result.readiness_score <= 0.66

    def test_result_has_timestamp(self):
        evidence = EvidenceObject(
            asset_id="AS-0001",
            component="engine",
            failure_risk=0.05,
            risk_level="LOW",
            anomaly=AnomalyEvidence(sensor="NONE", severity="LOW"),
            maintenance=MaintenanceEvidence(
                hours_since_service=50.0, inspection_status="COMPLETED"
            ),
            criticality="LOW",
            mission_impact="NONE",
        )
        result = evaluate([evidence])
        assert result.timestamp is not None
        assert len(result.timestamp) > 0

    def test_result_includes_evidence(self):
        evidence = EvidenceObject(
            asset_id="AS-0001",
            component="engine",
            failure_risk=0.05,
            risk_level="LOW",
            anomaly=AnomalyEvidence(sensor="NONE", severity="LOW"),
            maintenance=MaintenanceEvidence(
                hours_since_service=50.0, inspection_status="COMPLETED"
            ),
            criticality="LOW",
            mission_impact="NONE",
        )
        result = evaluate([evidence])
        assert len(result.evidence) == 1
        assert result.evidence[0].asset_id == "AS-0001"

    def test_mission_id_propagated(self):
        evidence = EvidenceObject(
            asset_id="AS-0001",
            component="engine",
            failure_risk=0.05,
            risk_level="LOW",
            anomaly=AnomalyEvidence(sensor="NONE", severity="LOW"),
            maintenance=MaintenanceEvidence(
                hours_since_service=50.0, inspection_status="COMPLETED"
            ),
            criticality="LOW",
            mission_impact="NONE",
        )
        result = evaluate([evidence], mission_id="MSN-001")
        assert result.mission_id == "MSN-001"

    def test_ready_result_has_positive_reason(self):
        evidence = EvidenceObject(
            asset_id="AS-0001",
            component="engine",
            failure_risk=0.05,
            risk_level="LOW",
            anomaly=AnomalyEvidence(sensor="NONE", severity="LOW"),
            maintenance=MaintenanceEvidence(
                hours_since_service=50.0, inspection_status="COMPLETED"
            ),
            criticality="LOW",
            mission_impact="NONE",
        )
        result = evaluate([evidence])
        assert result.readiness_status == "READY"
        assert len(result.reasons) > 0
        assert "acceptable" in result.reasons[0].lower()

    def test_not_ready_result_has_reason(self):
        """NOT_READY via scoring (high risk but below hard thresholds)."""
        evidence = EvidenceObject(
            asset_id="AS-0001",
            component="engine",
            failure_risk=0.90,
            risk_level="HIGH",
            anomaly=AnomalyEvidence(sensor="temperature", severity="HIGH"),
            maintenance=MaintenanceEvidence(
                hours_since_service=200.0, inspection_status="COMPLETED"
            ),
            criticality="LOW",  # LOW — hard rules won't fire
            mission_impact="HIGH",
        )
        result = evaluate([evidence])
        assert result.readiness_status == "NOT_READY"
        assert len(result.reasons) > 0


# ===========================================================================
# Multi-component aggregation tests
# ===========================================================================

class TestMultiComponentAggregation:
    def _make_evidence(
        self, asset_id: str, component: str, failure_risk: float,
        anomaly_severity: str, criticality: str,
        maintenance_status: str = "COMPLETED", mission_impact: str = "NONE"
    ) -> EvidenceObject:
        return EvidenceObject(
            asset_id=asset_id,
            component=component,
            failure_risk=failure_risk,
            risk_level="LOW",
            anomaly=AnomalyEvidence(sensor="vibration", severity=anomaly_severity),
            maintenance=MaintenanceEvidence(
                hours_since_service=100.0, inspection_status=maintenance_status
            ),
            criticality=criticality,
            mission_impact=mission_impact,
        )

    def test_worst_component_determines_status(self):
        """
        One healthy component + one high-risk component.
        The result must reflect the worst component.
        """
        healthy = self._make_evidence(
            "AS-0001", "engine", 0.05, "LOW", "LOW"
        )
        bad = self._make_evidence(
            "AS-0001", "hydraulics", 0.90, "HIGH", "LOW", mission_impact="HIGH"
        )
        result = evaluate([healthy, bad])
        # Score for bad: 0.40×0.90 + 0.25×1.0 + 0.20×0.25 + 0.15×1.0 = 0.36+0.25+0.05+0.15 = 0.81
        assert result.readiness_status == "NOT_READY"

    def test_two_healthy_components_are_ready(self):
        ev1 = self._make_evidence("AS-0001", "engine", 0.05, "LOW", "LOW")
        ev2 = self._make_evidence("AS-0001", "hydraulics", 0.08, "LOW", "LOW")
        result = evaluate([ev1, ev2])
        assert result.readiness_status == "READY"

    def test_hard_rule_fires_on_one_component_in_list(self):
        """If one component triggers a hard rule, the whole asset is NOT_READY."""
        healthy = self._make_evidence("AS-0001", "engine", 0.05, "LOW", "LOW")
        critical_overdue = self._make_evidence(
            "AS-0001", "main_bearing", 0.30, "LOW", "HIGH",
            maintenance_status="OVERDUE"
        )
        result = evaluate([healthy, critical_overdue])
        assert result.readiness_status == "NOT_READY"


# ===========================================================================
# AS-1047 canonical demo scenario (contract §23)
# ===========================================================================

class TestAS1047CanonicalScenario:
    """
    Verifies the end-to-end AS-1047 canonical scenario using fixtures.
    These tests use fixture values that match contract §23.
    The engine does NOT know about AS-1047 — it just processes evidence.
    """

    def test_as1047_generic_readiness_is_not_ready(
        self, as1047_prediction, as1047_component_info, as1047_maintenance_overdue
    ):
        """
        AS-1047 generic readiness:
        - failure_risk=0.87 + HIGH criticality → Rule 2 fires (0.87 > 0.75)
        - ALSO: OVERDUE + HIGH criticality → Rule 1 would fire
        - Either hard rule → NOT_READY
        """
        evidence = build_evidence(
            prediction=as1047_prediction,
            component_info=as1047_component_info,
            maintenance_info=as1047_maintenance_overdue,
            mission_impact="NONE",
        )
        result = evaluate([evidence])
        assert result.readiness_status == "NOT_READY"
        assert len(result.reasons) > 0

    def test_as1047_high_criticality_mission_is_not_ready(
        self, as1047_prediction, as1047_component_info, as1047_maintenance_overdue
    ):
        """
        AS-1047 + high-criticality mission (MSN-003):
        HIGH mission_impact set by MissionEvaluator before calling evaluate().
        Hard rules still fire → NOT_READY.
        """
        evidence = build_evidence(
            prediction=as1047_prediction,
            component_info=as1047_component_info,
            maintenance_info=as1047_maintenance_overdue,
            mission_impact="HIGH",   # MSN-003 → HIGH
        )
        result = evaluate([evidence], mission_id="MSN-003")
        assert result.readiness_status == "NOT_READY"
        assert result.mission_id == "MSN-003"

    def test_as1047_score_is_above_not_ready_threshold(
        self, as1047_prediction, as1047_component_info, as1047_maintenance_overdue
    ):
        """
        Score for AS-1047 with HIGH mission impact:
        0.40×0.87 + 0.25×1.0 + 0.20×1.0 + 0.15×1.0 = 0.948
        Must be above the NOT_READY threshold (0.66).
        """
        evidence = build_evidence(
            prediction=as1047_prediction,
            component_info=as1047_component_info,
            maintenance_info=as1047_maintenance_overdue,
            mission_impact="HIGH",
        )
        result = evaluate([evidence], mission_id="MSN-003")
        assert result.readiness_score > 0.66

    def test_as1047_result_carries_evidence(
        self, as1047_prediction, as1047_component_info, as1047_maintenance_overdue
    ):
        """Result must include the evidence objects for IBM Bob to explain."""
        evidence = build_evidence(
            prediction=as1047_prediction,
            component_info=as1047_component_info,
            maintenance_info=as1047_maintenance_overdue,
            mission_impact="HIGH",
        )
        result = evaluate([evidence], mission_id="MSN-003")
        assert len(result.evidence) == 1
        ev = result.evidence[0]
        assert ev.asset_id == "AS-1047"
        assert ev.component == "main_bearing"
        assert ev.failure_risk == pytest.approx(0.87)
        assert ev.criticality == "HIGH"
        assert ev.maintenance.inspection_status == "OVERDUE"

    def test_healthy_asset_generic_is_ready(
        self, healthy_prediction, healthy_component_info, healthy_maintenance_current
    ):
        """Healthy asset with COMPLETED maintenance and low risk → READY."""
        evidence = build_evidence(
            prediction=healthy_prediction,
            component_info=healthy_component_info,
            maintenance_info=healthy_maintenance_current,
            mission_impact="NONE",
        )
        result = evaluate([evidence])
        assert result.readiness_status == "READY"

    def test_medium_risk_generic_is_conditionally_ready(
        self, medium_prediction, medium_component_info, medium_maintenance_scheduled
    ):
        """
        Medium risk asset (failure_risk=0.50, MEDIUM anomaly/criticality):
        score = 0.40×0.50 + 0.25×0.60 + 0.20×0.60 + 0.15×0.0
              = 0.20 + 0.15 + 0.12 + 0.0 = 0.47
        → CONDITIONALLY_READY
        """
        evidence = build_evidence(
            prediction=medium_prediction,
            component_info=medium_component_info,
            maintenance_info=medium_maintenance_scheduled,
            mission_impact="NONE",
        )
        result = evaluate([evidence])
        assert result.readiness_status == "CONDITIONALLY_READY"
        expected_score = 0.40 * 0.50 + 0.25 * 0.60 + 0.20 * 0.60 + 0.15 * 0.0
        assert result.readiness_score == pytest.approx(expected_score, abs=1e-9)


# ===========================================================================
# Architectural separation guarantee
# ===========================================================================

class TestArchitecturalSeparation:
    """
    Verifies that the Readiness Engine does NOT import Member 2 code.

    The dependency direction must be:
        Evidence Layer → Readiness Engine
    NOT:
        Member 2 → Readiness Engine

    This test catches any accidental re-introduction of member2_ml imports
    into the readiness package.
    """

    def test_engine_does_not_import_member2(self):
        """
        readiness/engine.py must not import from member2_ml or
        services.prediction_service in any form.
        """
        import importlib
        import importlib.util
        import pathlib

        engine_path = pathlib.Path(__file__).parent.parent / "readiness" / "engine.py"
        source = engine_path.read_text(encoding="utf-8")

        forbidden_patterns = [
            "member2_ml",
            "prediction_service",
            "ComponentPredictionResult",
            "from services",
            "import services",
        ]
        for pattern in forbidden_patterns:
            assert pattern not in source, (
                f"readiness/engine.py must NOT import Member 2 code. "
                f"Found forbidden pattern: '{pattern}'. "
                f"The Readiness Engine must consume EvidenceObject only."
            )

    def test_engine_imports_evidence_layer_not_member2(self):
        """
        The readiness engine module's imported names must include EvidenceObject
        (from the Evidence Layer) and must NOT include ComponentPredictionResult.
        """
        import member3_readiness.readiness.engine as engine_module

        # EvidenceObject should be reachable (imported or used via type hints)
        from member3_readiness.evidence.models import EvidenceObject
        assert EvidenceObject is not None  # Evidence Layer is importable

        # ComponentPredictionResult must NOT be importable FROM the engine module
        assert not hasattr(engine_module, "ComponentPredictionResult"), (
            "readiness/engine.py must not expose ComponentPredictionResult. "
            "Member 2 types belong only in the Evidence Layer boundary."
        )

    def test_evaluate_accepts_evidence_object_not_prediction_result(self):
        """
        evaluate() must accept list[EvidenceObject], not ComponentPredictionResult.
        Passing an EvidenceObject directly works; the function signature must
        not expect Member 2 types.
        """
        from member3_readiness.readiness.engine import evaluate
        import inspect

        sig = inspect.signature(evaluate)
        params = list(sig.parameters.keys())
        assert "evidence_list" in params, (
            "evaluate() must have an 'evidence_list' parameter accepting EvidenceObject instances."
        )
        # Verify it actually runs with an EvidenceObject list (not a Member 2 type)
        evidence = EvidenceObject(
            asset_id="AS-SEP-TEST",
            component="test_component",
            failure_risk=0.10,
            risk_level="LOW",
            anomaly=AnomalyEvidence(sensor="NONE", severity="LOW"),
            maintenance=MaintenanceEvidence(
                hours_since_service=50.0, inspection_status="COMPLETED"
            ),
            criticality="LOW",
            mission_impact="NONE",
        )
        result = evaluate([evidence])
        assert result.asset_id == "AS-SEP-TEST"


# ===========================================================================
# Determinism guarantee (prompt requirement #17 / #18)
# ===========================================================================

class TestDeterminism:
    """
    Verifies that the Readiness Engine is deterministic:
        - Same EvidenceObject always produces the same result.
        - Different EvidenceObjects produce different results when expected.
    """

    def _make_evidence(
        self,
        failure_risk: float = 0.30,
        anomaly_severity: str = "LOW",
        criticality: str = "LOW",
        maintenance_status: str = "COMPLETED",
        mission_impact: str = "NONE",
    ) -> EvidenceObject:
        return EvidenceObject(
            asset_id="AS-DET-TEST",
            component="test_component",
            failure_risk=failure_risk,
            risk_level="LOW",
            anomaly=AnomalyEvidence(sensor="vibration", severity=anomaly_severity),
            maintenance=MaintenanceEvidence(
                hours_since_service=100.0, inspection_status=maintenance_status
            ),
            criticality=criticality,
            mission_impact=mission_impact,
        )

    def test_same_evidence_produces_same_score(self):
        """Calling evaluate() twice with identical evidence yields identical scores."""
        evidence = self._make_evidence(failure_risk=0.45, anomaly_severity="MEDIUM")
        result_a = evaluate([evidence])
        result_b = evaluate([evidence])
        assert result_a.readiness_score == result_b.readiness_score

    def test_same_evidence_produces_same_status(self):
        """Calling evaluate() twice with identical evidence yields identical status."""
        evidence = self._make_evidence(failure_risk=0.45, anomaly_severity="MEDIUM")
        result_a = evaluate([evidence])
        result_b = evaluate([evidence])
        assert result_a.readiness_status == result_b.readiness_status

    def test_same_evidence_produces_same_reasons(self):
        """Calling evaluate() twice with identical evidence yields identical reasons."""
        evidence = self._make_evidence(failure_risk=0.45, anomaly_severity="MEDIUM")
        result_a = evaluate([evidence])
        result_b = evaluate([evidence])
        assert result_a.reasons == result_b.reasons

    def test_different_failure_risk_produces_different_scores(self):
        """Higher failure_risk must produce a higher readiness risk score."""
        low_risk = self._make_evidence(failure_risk=0.10)
        high_risk = self._make_evidence(failure_risk=0.90)
        result_low = evaluate([low_risk])
        result_high = evaluate([high_risk])
        assert result_high.readiness_score > result_low.readiness_score

    def test_different_evidence_different_status_when_expected(self):
        """
        A healthy component → READY.
        A high-risk component (below hard-rule thresholds, score-based path) → NOT_READY.
        """
        ready_evidence = self._make_evidence(
            failure_risk=0.05, anomaly_severity="LOW",
            criticality="LOW", mission_impact="NONE"
        )
        not_ready_evidence = self._make_evidence(
            failure_risk=0.90, anomaly_severity="HIGH",
            criticality="LOW", mission_impact="HIGH"  # LOW criticality — no hard rules
        )
        result_ready = evaluate([ready_evidence])
        result_not_ready = evaluate([not_ready_evidence])
        assert result_ready.readiness_status == "READY"
        assert result_not_ready.readiness_status == "NOT_READY"

    def test_readiness_score_is_numeric_float_in_range(self):
        """readiness_score must be a float in [0.0, 1.0] (prompt requirement #16)."""
        evidence = self._make_evidence(failure_risk=0.50, anomaly_severity="MEDIUM")
        result = evaluate([evidence])
        assert isinstance(result.readiness_score, float)
        assert 0.0 <= result.readiness_score <= 1.0


# ===========================================================================
# Hard rule overrides weighted score (prompt requirement #11)
# ===========================================================================

class TestHardRuleOverridesScore:
    """
    Explicit proof that hard rules force NOT_READY even when the weighted
    score alone would produce READY or CONDITIONALLY_READY.

    Requirement: hard rule triggers → NOT_READY regardless of score value.
    """

    def test_rule1_overrides_low_weighted_score(self):
        """
        A component with low failure_risk (0.10) that would score READY
        via the weighted formula must still return NOT_READY if OVERDUE
        and HIGH criticality (Rule 1 fires).

        Expected weighted score (if scoring ran):
            0.40×0.10 + 0.25×0.25 + 0.20×1.0 + 0.15×0.0
            = 0.04 + 0.0625 + 0.20 + 0.0 = 0.3025  → would be READY

        But Rule 1 fires first → NOT_READY.
        """
        evidence = EvidenceObject(
            asset_id="AS-OVERRIDE-TEST",
            component="main_bearing",
            failure_risk=0.10,   # deliberately LOW — would score READY alone
            risk_level="LOW",
            anomaly=AnomalyEvidence(sensor="NONE", severity="LOW"),
            maintenance=MaintenanceEvidence(
                hours_since_service=500.0,
                inspection_status="OVERDUE",   # triggers Rule 1
            ),
            criticality="HIGH",   # HIGH → Rule 1 applies
            mission_impact="NONE",
        )
        result = evaluate([evidence])
        # The hard rule must fire and override the score-based READY verdict
        assert result.readiness_status == "NOT_READY", (
            "Rule 1 (OVERDUE + HIGH criticality) must force NOT_READY "
            "even when the weighted score would produce READY."
        )
        assert len(result.reasons) > 0
        assert any("overdue" in r.lower() or "inspection" in r.lower()
                   for r in result.reasons)

    def test_rule2_overrides_low_anomaly_score(self):
        """
        A component with LOW anomaly and LOW mission_impact that would
        score below NOT_READY threshold must still return NOT_READY if
        failure_risk > 0.75 and criticality is HIGH (Rule 2 fires).

        Expected weighted score (if scoring ran):
            0.40×0.80 + 0.25×0.25 + 0.20×1.0 + 0.15×0.0
            = 0.32 + 0.0625 + 0.20 + 0.0 = 0.5825 → would be CONDITIONALLY_READY

        But Rule 2 fires first → NOT_READY.
        """
        evidence = EvidenceObject(
            asset_id="AS-OVERRIDE-TEST",
            component="engine",
            failure_risk=0.80,   # > 0.75 threshold → Rule 2 fires
            risk_level="HIGH",
            anomaly=AnomalyEvidence(sensor="NONE", severity="LOW"),  # LOW anomaly
            maintenance=MaintenanceEvidence(
                hours_since_service=100.0,
                inspection_status="COMPLETED",   # not OVERDUE — Rule 1 won't fire
            ),
            criticality="HIGH",   # HIGH → Rule 2 applies
            mission_impact="NONE",  # no mission boost
        )
        result = evaluate([evidence])
        assert result.readiness_status == "NOT_READY", (
            "Rule 2 (failure_risk > threshold + HIGH criticality) must force NOT_READY "
            "even when the weighted score would produce CONDITIONALLY_READY."
        )
        assert len(result.reasons) > 0
        assert any("threshold" in r.lower() or "failure risk" in r.lower()
                   for r in result.reasons)

    def test_hard_rule_reason_is_specific_not_vague(self):
        """
        Reasons from hard rules must be specific — not 'Asset is risky.'
        They must reference the actual component and condition.
        """
        evidence = EvidenceObject(
            asset_id="AS-REASON-TEST",
            component="gearbox",
            failure_risk=0.10,
            risk_level="LOW",
            anomaly=AnomalyEvidence(sensor="NONE", severity="LOW"),
            maintenance=MaintenanceEvidence(
                hours_since_service=300.0,
                inspection_status="OVERDUE",
            ),
            criticality="HIGH",
            mission_impact="NONE",
        )
        result = evaluate([evidence])
        assert result.readiness_status == "NOT_READY"
        reason = result.reasons[0]
        # Must mention the component, not be a generic string
        assert "gearbox" in reason.lower(), (
            f"Hard-rule reason must name the specific component. Got: '{reason}'"
        )
        # Must not be vague
        assert reason.lower() not in ("asset is risky.", "not ready.", "risk detected."), (
            f"Hard-rule reason must not be vague. Got: '{reason}'"
        )

    def test_generic_readiness_mission_id_none(self):
        """
        Explicit test for generic readiness (mission_id=None).
        The engine must work without any mission context.
        """
        evidence = EvidenceObject(
            asset_id="AS-GENERIC-TEST",
            component="rotor",
            failure_risk=0.20,
            risk_level="LOW",
            anomaly=AnomalyEvidence(sensor="NONE", severity="LOW"),
            maintenance=MaintenanceEvidence(
                hours_since_service=80.0, inspection_status="COMPLETED"
            ),
            criticality="LOW",
            mission_impact="NONE",
        )
        result = evaluate([evidence], mission_id=None)
        assert result.mission_id is None
        assert result.readiness_status in ("READY", "CONDITIONALLY_READY", "NOT_READY")
        assert isinstance(result.readiness_score, float)
        assert 0.0 <= result.readiness_score <= 1.0
