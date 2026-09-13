"""
AssetSentinel — Readiness Engine
Member 3 (Tisha) | src/backend/member3_readiness/readiness/engine.py

Purpose:
    Deterministic readiness evaluation from a list of EvidenceObject instances.

    The Readiness Engine is the ONLY authority for readiness verdicts.

    It cannot be overridden by:
        - IBM Bob
        - The ML models
        - The frontend
        - Any copilot or external agent

Architecture:
    1. Hard rules execute FIRST (contract §14).
       First matching rule immediately returns NOT_READY.
    2. If no hard rule fires, the weighted readiness risk score is computed
       (contract §15) using READINESS_CONFIG.weights.
    3. The score is mapped to a status using READINESS_CONFIG.thresholds.
    4. A ReadinessResult is returned with score, status, reasons, and evidence.

Hard rules (contract §14):
    Rule 1: Overdue mandatory inspection on a critical (HIGH) component → NOT_READY
    Rule 2: Critical component failure_risk > hard threshold → NOT_READY
    Rule 3 (mission-aware): Mission-required component unavailable → NOT_READY
             Rule 3 is handled by MissionEvaluator (missions/evaluator.py),
             which sets mission_impact and calls evaluate() here.

Score formula (contract §15):
    score = (
        0.40 × failure_risk
      + 0.25 × normalize(anomaly.severity)
      + 0.20 × normalize(criticality)
      + 0.15 × normalize(mission_impact)
    )

    normalize() maps "NONE"→0.0, "LOW"→0.25, "MEDIUM"→0.60, "HIGH"→1.0.
    Weights and normalization values live in config/settings.py ONLY.

Public API:
    evaluate(evidence_list, mission_id=None) → ReadinessResult

    Callers pass an already-assembled list of EvidenceObject instances
    (produced by the Evidence Layer). The engine does NOT call ML inference.

Ownership:
    - Only Member 3 modifies this file.
    - Member 1 calls evaluate() from the /api/assets/{asset_id}/readiness endpoint.
    - IBM Bob receives the ReadinessResult via MCP and explains it.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from member3_readiness.config.settings import (
    LEVEL_TO_FLOAT,
    READINESS_CONFIG,
)
from member3_readiness.evidence.models import (
    CriticalityLevel,
    EvidenceObject,
    MissionImpactLevel,
)
from member3_readiness.readiness.models import ReadinessResult, ReadinessStatus


# ---------------------------------------------------------------------------
# Internal helpers — normalization
# ---------------------------------------------------------------------------

def _normalize(level: str) -> float:
    """
    Convert a categorical level string to a 0.0–1.0 float.

    Uses LEVEL_TO_FLOAT from config/settings.py.
    Raises KeyError if an unrecognized level is passed — callers should
    only pass validated Literal values from the Pydantic models.
    """
    try:
        return LEVEL_TO_FLOAT[level]
    except KeyError:
        raise ValueError(
            f"Cannot normalize level '{level}'. "
            f"Valid values: {list(LEVEL_TO_FLOAT.keys())}."
        )


def _is_critical(criticality: CriticalityLevel) -> bool:
    """Return True if the component criticality is HIGH (the only 'critical' tier)."""
    return criticality == "HIGH"


# ---------------------------------------------------------------------------
# Hard rule evaluators (contract §14)
# ---------------------------------------------------------------------------

def _check_hard_rule_1(evidence: EvidenceObject) -> Optional[str]:
    """
    Rule 1: Overdue mandatory inspection on a critical component → NOT_READY.

    Returns a human-readable reason string if the rule fires, else None.
    """
    if (
        _is_critical(evidence.criticality)
        and evidence.maintenance.inspection_status == "OVERDUE"
    ):
        return (
            f"Mandatory inspection overdue on critical component '{evidence.component}' "
            f"({evidence.maintenance.hours_since_service:.0f} hours since last service)."
        )
    return None


def _check_hard_rule_2(evidence: EvidenceObject) -> Optional[str]:
    """
    Rule 2: Critical component failure_risk exceeds configured hard threshold → NOT_READY.

    Returns a human-readable reason string if the rule fires, else None.
    """
    threshold = READINESS_CONFIG.hard_rules.critical_failure_risk_hard_threshold
    if _is_critical(evidence.criticality) and evidence.failure_risk > threshold:
        return (
            f"Critical component '{evidence.component}' failure risk "
            f"({evidence.failure_risk:.0%}) exceeds the configured threshold "
            f"({threshold:.0%})."
        )
    return None


# ---------------------------------------------------------------------------
# Weighted score computation (contract §15)
# ---------------------------------------------------------------------------

def _compute_component_score(evidence: EvidenceObject) -> float:
    """
    Compute the readiness risk score for a single EvidenceObject.

    Formula (contract §15):
        score = 0.40 × failure_risk
              + 0.25 × normalize(anomaly.severity)
              + 0.20 × normalize(criticality)
              + 0.15 × normalize(mission_impact)

    Higher score = higher risk = worse readiness.
    """
    w = READINESS_CONFIG.weights
    return (
        w.failure_risk     * evidence.failure_risk
        + w.anomaly_severity * _normalize(evidence.anomaly.severity)
        + w.criticality      * _normalize(evidence.criticality)
        + w.mission_impact   * _normalize(evidence.mission_impact)
    )


def _aggregate_scores(scores: list[float]) -> float:
    """
    Aggregate per-component scores into a single asset-level readiness score.

    Strategy: take the maximum per-component score.
    Rationale: an asset is only as ready as its worst component.
    A failing bearing makes the whole platform unready regardless of the
    other components' scores.
    """
    if not scores:
        return 0.0
    return max(scores)


def _score_to_status(
    score: float, mission_threshold: Optional[float] = None
) -> ReadinessStatus:
    """
    Map a readiness risk score to a ReadinessStatus using configured thresholds.

    Contract §15 thresholds:
        0.00–0.34 → READY
        0.35–0.66 → CONDITIONALLY_READY
        0.67–1.00 → NOT_READY
        
    If a mission specifies a custom readiness_threshold (from contract §11),
    it overrides the NOT_READY boundary.
    """
    t = READINESS_CONFIG.thresholds
    
    not_ready_threshold = mission_threshold if mission_threshold is not None else t.conditionally_ready_max
    
    if score > not_ready_threshold:
        return "NOT_READY"
        
    if score <= t.ready_max:
        return "READY"
        
    return "CONDITIONALLY_READY"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def evaluate(
    evidence_list: list[EvidenceObject],
    mission_id: Optional[str] = None,
    mission_threshold: Optional[float] = None,
) -> ReadinessResult:
    """
    Evaluate asset readiness from a list of EvidenceObject instances.

    This is the ONLY entry point for readiness evaluation.

    Algorithm:
        1. For each EvidenceObject, check hard rules in order (Rule 1, Rule 2).
           If any rule fires, immediately return NOT_READY with the reason.
        2. Compute the weighted readiness risk score for each component.
        3. Aggregate scores (take the maximum — worst-component strategy).
        4. Map the aggregate score to a ReadinessStatus.
        5. Collect all per-component reason strings for CONDITIONALLY_READY.
        6. Return a ReadinessResult.

    Args:
        evidence_list:  List of EvidenceObject instances assembled by the
                        Evidence Layer for the asset being evaluated.
                        Must contain at least one item.
        mission_id:     Optional mission ID for mission-specific evaluation.
                        When provided, the evidence list should already have
                        mission_impact set by the MissionEvaluator — this
                        engine does not look up missions independently.

    Returns:
        ReadinessResult with readiness_score, readiness_status, reasons,
        evidence, and timestamp.

    Raises:
        ValueError  If evidence_list is empty.
    """
    if not evidence_list:
        raise ValueError(
            "evidence_list must contain at least one EvidenceObject. "
            "Cannot evaluate readiness without evidence."
        )

    asset_id = evidence_list[0].asset_id

    # --- Step 1: Hard rules (first match wins; return immediately) ---
    for evidence in evidence_list:
        hard_reason = _check_hard_rule_1(evidence)
        if hard_reason:
            return ReadinessResult(
                asset_id=asset_id,
                mission_id=mission_id,
                readiness_score=_aggregate_scores(
                    [_compute_component_score(e) for e in evidence_list]
                ),
                readiness_status="NOT_READY",
                reasons=[hard_reason],
                evidence=evidence_list,
                timestamp=datetime.now(tz=timezone.utc).isoformat(),
            )

        hard_reason = _check_hard_rule_2(evidence)
        if hard_reason:
            return ReadinessResult(
                asset_id=asset_id,
                mission_id=mission_id,
                readiness_score=_aggregate_scores(
                    [_compute_component_score(e) for e in evidence_list]
                ),
                readiness_status="NOT_READY",
                reasons=[hard_reason],
                evidence=evidence_list,
                timestamp=datetime.now(tz=timezone.utc).isoformat(),
            )

    # --- Step 2–4: Weighted score computation ---
    component_scores = [_compute_component_score(e) for e in evidence_list]
    aggregate_score = _aggregate_scores(component_scores)
    status = _score_to_status(aggregate_score, mission_threshold)

    # --- Step 5: Collect human-readable reasons ---
    reasons = _build_score_reasons(evidence_list, component_scores, status)

    return ReadinessResult(
        asset_id=asset_id,
        mission_id=mission_id,
        readiness_score=aggregate_score,
        readiness_status=status,
        reasons=reasons,
        evidence=evidence_list,
        timestamp=datetime.now(tz=timezone.utc).isoformat(),
    )


# ---------------------------------------------------------------------------
# Reason string builder (score-based path)
# ---------------------------------------------------------------------------

def _build_score_reasons(
    evidence_list: list[EvidenceObject],
    scores: list[float],
    status: ReadinessStatus,
) -> list[str]:
    """
    Build human-readable reason strings for the scored readiness result.

    For READY: returns a single positive confirmation string.
    For CONDITIONALLY_READY / NOT_READY: returns one reason per component
    whose score is above the READY threshold, describing the dominant factor.
    """
    if status == "READY":
        return ["All components within acceptable readiness parameters."]

    reasons: list[str] = []
    ready_max = READINESS_CONFIG.thresholds.ready_max

    for evidence, score in zip(evidence_list, scores):
        if score <= ready_max:
            continue  # This component is within acceptable range

        # Build a reason that describes the most impactful contributing factor
        factors: list[tuple[float, str]] = [
            (
                READINESS_CONFIG.weights.failure_risk * evidence.failure_risk,
                f"failure risk {evidence.failure_risk:.0%} ({evidence.risk_level})"
            ),
            (
                READINESS_CONFIG.weights.anomaly_severity
                * _normalize(evidence.anomaly.severity),
                f"{evidence.anomaly.severity.lower()} anomaly severity on "
                f"{evidence.anomaly.sensor} sensor"
            ),
            (
                READINESS_CONFIG.weights.criticality
                * _normalize(evidence.criticality),
                f"{evidence.criticality.lower()} component criticality"
            ),
            (
                READINESS_CONFIG.weights.mission_impact
                * _normalize(evidence.mission_impact),
                f"{evidence.mission_impact.lower()} mission impact"
            ),
        ]

        # Sort by weighted contribution descending; include top contributing factors
        factors.sort(key=lambda x: x[0], reverse=True)
        top_factors = [f[1] for f in factors if f[0] > 0.0]

        if not top_factors:
            reasons.append(
                f"Component '{evidence.component}' score {score:.2f} exceeds "
                f"readiness threshold."
            )
        else:
            reasons.append(
                f"Component '{evidence.component}' readiness risk score {score:.2f}: "
                + ", ".join(top_factors[:3]) + "."
            )

    return reasons if reasons else [f"Readiness risk score {max(scores):.2f} exceeds threshold."]
