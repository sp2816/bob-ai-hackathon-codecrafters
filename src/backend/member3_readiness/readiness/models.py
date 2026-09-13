"""
AssetSentinel — Readiness Engine: Output Models
Member 3 (Tisha) | src/backend/member3_readiness/readiness/models.py

Purpose:
    Defines the Pydantic output model produced by the Readiness Engine:
        ReadinessResult — the authoritative readiness verdict for an asset.

    These models represent the OUTPUT of the Readiness Engine. They are
    distinct from the Evidence Layer input models (evidence/models.py).

Contract alignment:
    All field names follow data-contracts.md §13 (Readiness Result Contract).

Ownership rules:
    - Only Member 3 modifies this file.
    - Member 1 wraps ReadinessResult in API response schemas.
    - Member 4 renders readiness_status/readiness_score/reasons from the API.
    - Do NOT add ML, sensor, or maintenance-record fields here.
    - IBM Bob receives this result via MCP and explains it — never modifies it.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field

from member3_readiness.evidence.models import EvidenceObject


# ---------------------------------------------------------------------------
# Readiness status enum (contract §13 / §18)
# ---------------------------------------------------------------------------

ReadinessStatus = Literal["READY", "CONDITIONALLY_READY", "NOT_READY"]


# ---------------------------------------------------------------------------
# Readiness Result (contract §13)
# ---------------------------------------------------------------------------

class ReadinessResult(BaseModel):
    """
    The authoritative readiness verdict produced by the Readiness Engine.

    This is the ONLY object that carries readiness_status and readiness_score.
    Frontend and IBM Bob consume this — they do NOT re-derive these values.

    Contract §13 fields:
        asset_id         — asset being evaluated
        mission_id       — None for generic (non-mission-specific) readiness
        readiness_score  — weighted risk score 0.0–1.0 (higher = more risk)
        readiness_status — READY | CONDITIONALLY_READY | NOT_READY
        reasons          — human-readable explanation strings
        evidence         — list of EvidenceObject instances that led to this verdict
        timestamp        — UTC ISO-8601 string
    """

    asset_id: str = Field(
        ...,
        description="Canonical asset identifier string (contract §3). Example: 'AS-1047'.",
    )
    mission_id: Optional[str] = Field(
        default=None,
        description=(
            "Mission ID for mission-specific readiness evaluation. "
            "None / null for generic asset-level readiness."
        ),
    )
    readiness_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "Weighted readiness risk score in [0.0, 1.0]. "
            "Higher score = higher risk = worse readiness. "
            "Computed by the Readiness Engine; never set by the frontend or IBM Bob."
        ),
    )
    readiness_status: ReadinessStatus = Field(
        ...,
        description=(
            "Readiness verdict: READY | CONDITIONALLY_READY | NOT_READY. "
            "Determined deterministically by the Readiness Engine. "
            "Cannot be overridden by IBM Bob, ML models, or the frontend."
        ),
    )
    reasons: list[str] = Field(
        default_factory=list,
        description=(
            "Ordered list of human-readable reason strings explaining "
            "how the readiness verdict was reached. "
            "Examples: 'Bearing inspection is overdue', "
            "'Critical component failure risk exceeds threshold'."
        ),
    )
    evidence: list[EvidenceObject] = Field(
        default_factory=list,
        description=(
            "The EvidenceObject instances that were evaluated to produce this result. "
            "Included so IBM Bob and the frontend can display the evidence chain."
        ),
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc).isoformat(),
        description="UTC ISO-8601 timestamp at which the readiness result was computed.",
    )
