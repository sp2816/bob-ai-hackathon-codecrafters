"""
AssetSentinel — Maintenance Priority Engine
Member 3 (Tisha) | src/backend/member3_readiness/maintenance/priority_engine.py

Purpose:
    Ranks fleet-wide maintenance actions by computed priority score.

    The Maintenance Priority Engine:
        1. Receives a list of EvidenceObject instances (one per asset-component).
        2. Computes a priority score for each using the weighted formula (contract §16).
        3. Derives urgency from the component's maintenance status.
        4. Generates a human-readable action and reason for each recommendation.
        5. Sorts by priority_score descending.
        6. Returns a ranked list of MaintenanceRecommendation instances.

    Priority formula (contract §16):
        priority_score =
            w1 × failure_risk
          + w2 × normalize(criticality)
          + w3 × normalize(mission_impact)
          + w4 × urgency_score

    Weights live exclusively in MAINTENANCE_CONFIG (config/settings.py).
    Normalization values live exclusively in LEVEL_TO_FLOAT (config/settings.py).
    Urgency scores live exclusively in MAINTENANCE_STATUS_TO_URGENCY (config/settings.py).

Architecture rule:
    Do NOT sort simply by failure_probability (contract §16).
    The full weighted formula must drive all rankings.

Public API:
    rank_maintenance(evidence_list, component_id_map) → list[MaintenanceRecommendation]

    component_id_map: dict[tuple[asset_id, component_type], component_id]
        Provided by Member 1 / database layer.
        The EvidenceObject carries component_type but NOT component_id
        (by contract §10 design). The caller must supply this mapping so
        the recommendation can include component_id for API consumers.

Ownership:
    - Only Member 3 modifies this file.
    - Member 1 calls rank_maintenance() from GET /api/maintenance/priorities.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from member3_readiness.config.settings import (
    LEVEL_TO_FLOAT,
    MAINTENANCE_CONFIG,
    MAINTENANCE_STATUS_TO_URGENCY,
)
from member3_readiness.evidence.models import EvidenceObject
from member3_readiness.maintenance.models import MaintenanceRecommendation, UrgencyLevel


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_urgency_score(inspection_status: str) -> float:
    """
    Map maintenance inspection_status to an urgency score 0.0–1.0.
    Uses MAINTENANCE_STATUS_TO_URGENCY from config/settings.py.
    """
    return MAINTENANCE_STATUS_TO_URGENCY.get(inspection_status, 0.0)


def _get_urgency_level(inspection_status: str) -> UrgencyLevel:
    """
    Map maintenance inspection_status to a categorical UrgencyLevel.
    OVERDUE → HIGH, SCHEDULED → MEDIUM, COMPLETED → LOW.
    """
    urgency_map: dict[str, UrgencyLevel] = {
        "OVERDUE": "HIGH",
        "SCHEDULED": "MEDIUM",
        "COMPLETED": "LOW",
    }
    return urgency_map.get(inspection_status, "LOW")


def _compute_priority_score(evidence: EvidenceObject) -> float:
    """
    Compute the maintenance priority score for one EvidenceObject.

    Formula (contract §16):
        priority_score =
            w1 × failure_risk
          + w2 × normalize(criticality)
          + w3 × normalize(mission_impact)
          + w4 × urgency_score

    Higher score = higher priority.
    """
    w = MAINTENANCE_CONFIG.weights
    urgency_score = _get_urgency_score(evidence.maintenance.inspection_status)

    return (
        w.failure_risk   * evidence.failure_risk
        + w.criticality    * LEVEL_TO_FLOAT[evidence.criticality]
        + w.mission_impact * LEVEL_TO_FLOAT[evidence.mission_impact]
        + w.urgency        * urgency_score
    )


def _build_action(evidence: EvidenceObject) -> str:
    """Generate a human-readable maintenance action description."""
    status = evidence.maintenance.inspection_status
    component = evidence.component.replace("_", " ").title()

    if status == "OVERDUE":
        return f"Immediate inspection and servicing of {component} — inspection overdue."
    if evidence.risk_level == "HIGH":
        return f"Inspect and replace {component} — high failure risk detected."
    if evidence.risk_level == "MEDIUM":
        return f"Inspect {component} and assess condition — elevated failure risk."
    return f"Schedule routine inspection of {component}."


def _build_reason(evidence: EvidenceObject, priority_score: float) -> str:
    """
    Build a human-readable explanation of why this component was ranked
    at its priority, referencing the contributing factors.
    """
    w = MAINTENANCE_CONFIG.weights
    factors: list[tuple[float, str]] = [
        (
            w.failure_risk * evidence.failure_risk,
            f"failure risk {evidence.failure_risk:.0%} ({evidence.risk_level})"
        ),
        (
            w.criticality * LEVEL_TO_FLOAT[evidence.criticality],
            f"{evidence.criticality.lower()} component criticality"
        ),
        (
            w.mission_impact * LEVEL_TO_FLOAT[evidence.mission_impact],
            f"{evidence.mission_impact.lower()} mission impact"
        ),
        (
            w.urgency * _get_urgency_score(evidence.maintenance.inspection_status),
            f"maintenance {evidence.maintenance.inspection_status.lower()}"
        ),
    ]

    # Sort by contribution descending; include top non-zero factors
    factors.sort(key=lambda x: x[0], reverse=True)
    top_factors = [f[1] for f in factors if f[0] > 0.0]

    factor_text = ", ".join(top_factors[:3]) if top_factors else "compound risk factors"
    return (
        f"Priority score {priority_score:.3f}: {factor_text}."
    )


# ---------------------------------------------------------------------------
# Recommendation ID generation
# ---------------------------------------------------------------------------

def _make_recommendation_id(rank: int, asset_id: str, component: str) -> str:
    """
    Generate a deterministic recommendation ID from rank, asset, and component.
    Example: REC-001-AS1047-main_bearing
    """
    asset_short = asset_id.replace("-", "")
    comp_short = component.replace("_", "-").lower()
    return f"REC-{rank:03d}-{asset_short}-{comp_short}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def rank_maintenance(
    evidence_list: list[EvidenceObject],
    component_id_map: dict[tuple[str, str], str] | None = None,
) -> list[MaintenanceRecommendation]:
    """
    Compute a ranked fleet-wide maintenance priority list.

    Takes a list of EvidenceObject instances (one per asset-component pairing)
    and returns them ranked by priority_score descending.

    Args:
        evidence_list:      List of EvidenceObject instances from the Evidence Layer.
                            Typically covers all components across the fleet.
                            May contain mission-enriched or generic evidence.
                            Must not be empty.
        component_id_map:   Optional dict mapping (asset_id, component_type) → component_id.
                            EvidenceObject.component is the type (e.g. "main_bearing"),
                            not the ID (e.g. "BRG-1047"). The recommendation includes
                            component_id for API consumers (Member 1 provides this mapping).
                            If None or a key is missing, component_id defaults to
                            f"{asset_id}-{component_type}" as a placeholder.

    Returns:
        list[MaintenanceRecommendation] sorted by priority_score descending,
        with integer priority ranks 1…N assigned.

    Raises:
        ValueError  If evidence_list is empty.
    """
    if not evidence_list:
        raise ValueError(
            "evidence_list must not be empty. "
            "Cannot rank maintenance without evidence."
        )

    cid_map = component_id_map or {}

    # --- Compute scores for each component ---
    scored: list[tuple[float, EvidenceObject]] = [
        (_compute_priority_score(ev), ev)
        for ev in evidence_list
    ]

    # --- Sort descending by score (higher priority = rank 1) ---
    scored.sort(key=lambda x: x[0], reverse=True)

    # --- Build ranked recommendations ---
    recommendations: list[MaintenanceRecommendation] = []
    for rank, (score, evidence) in enumerate(scored, start=1):
        component_id_key = (evidence.asset_id, evidence.component)
        component_id = cid_map.get(
            component_id_key,
            f"{evidence.asset_id}-{evidence.component}",  # placeholder if not supplied
        )

        rec = MaintenanceRecommendation(
            recommendation_id=_make_recommendation_id(rank, evidence.asset_id, evidence.component),
            asset_id=evidence.asset_id,
            component_id=component_id,
            component=evidence.component,
            priority=rank,
            priority_score=score,
            action=_build_action(evidence),
            reason=_build_reason(evidence, score),
            risk=evidence.risk_level,
            mission_impact=evidence.mission_impact,
            urgency=_get_urgency_level(evidence.maintenance.inspection_status),
            status="OPEN",
        )
        recommendations.append(rec)

    return recommendations
