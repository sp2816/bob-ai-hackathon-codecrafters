"""
AssetSentinel — Readiness & Maintenance Configuration
Member 3 (Tisha) | src/backend/member3_readiness/config/settings.py

Purpose:
    Single source of truth for ALL configurable constants used by:
        - Readiness Engine
        - Maintenance Priority Engine
        - Mission Evaluator

    Contract §15 requires that weights and thresholds exist in ONE
    configuration location and are NOT duplicated throughout the codebase.

    This module defines a frozen dataclass so values are immutable at
    runtime (prevents accidental mutation during request handling).

Usage:
    from member3_readiness.config.settings import READINESS_CONFIG, MAINTENANCE_CONFIG

    score = READINESS_CONFIG.weights.failure_risk * evidence.failure_risk + ...

Ownership:
    - Only Member 3 modifies this file.
    - Member 1 may read these values when assembling API responses.
    - Do NOT duplicate any of these constants elsewhere in Member 3's code.
"""

from __future__ import annotations

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Readiness score weights (contract §15)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ReadinessWeights:
    """
    Weights for the readiness risk score formula (contract §15).

    Formula:
        score = (
            failure_risk     × evidence.failure_risk
          + anomaly_severity  × normalized(evidence.anomaly.severity)
          + criticality       × normalized(evidence.criticality)
          + mission_impact    × normalized(evidence.mission_impact)
        )

    All weights MUST sum to 1.0.
    """

    failure_risk: float = 0.40
    anomaly_severity: float = 0.25
    criticality: float = 0.20
    mission_impact: float = 0.15

    def __post_init__(self) -> None:
        total = (
            self.failure_risk
            + self.anomaly_severity
            + self.criticality
            + self.mission_impact
        )
        if abs(total - 1.0) > 1e-9:
            raise ValueError(
                f"ReadinessWeights must sum to 1.0, got {total}. "
                "Adjust weights before changing them."
            )


@dataclass(frozen=True)
class ReadinessThresholds:
    """
    Score thresholds that determine readiness status (contract §15).

    A score in [0.0, ready_max] → READY
    A score in (ready_max, conditionally_ready_max] → CONDITIONALLY_READY
    A score in (conditionally_ready_max, 1.0] → NOT_READY
    """

    ready_max: float = 0.34
    conditionally_ready_max: float = 0.66

    def __post_init__(self) -> None:
        if not (0.0 < self.ready_max < self.conditionally_ready_max < 1.0):
            raise ValueError(
                f"Thresholds must satisfy 0 < ready_max < conditionally_ready_max < 1.0. "
                f"Got ready_max={self.ready_max}, "
                f"conditionally_ready_max={self.conditionally_ready_max}."
            )


@dataclass(frozen=True)
class HardRuleThresholds:
    """
    Thresholds used by the hard rules that fire BEFORE weighted scoring
    (contract §14).

    Rule 2: A critical component whose failure_risk exceeds
    critical_failure_risk_hard_threshold causes NOT_READY regardless of score.
    """

    # Rule 2: failure_risk threshold for critical components
    critical_failure_risk_hard_threshold: float = 0.75

    def __post_init__(self) -> None:
        if not (0.0 < self.critical_failure_risk_hard_threshold <= 1.0):
            raise ValueError(
                f"critical_failure_risk_hard_threshold must be in (0.0, 1.0], "
                f"got {self.critical_failure_risk_hard_threshold}."
            )


@dataclass(frozen=True)
class ReadinessConfig:
    """Top-level readiness configuration bundle."""

    weights: ReadinessWeights = None          # type: ignore[assignment]
    thresholds: ReadinessThresholds = None    # type: ignore[assignment]
    hard_rules: HardRuleThresholds = None     # type: ignore[assignment]

    def __post_init__(self) -> None:
        # Replace None sentinels with defaults (frozen dataclass workaround)
        if self.weights is None:
            object.__setattr__(self, "weights", ReadinessWeights())
        if self.thresholds is None:
            object.__setattr__(self, "thresholds", ReadinessThresholds())
        if self.hard_rules is None:
            object.__setattr__(self, "hard_rules", HardRuleThresholds())


# ---------------------------------------------------------------------------
# Maintenance priority weights (contract §16)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MaintenanceWeights:
    """
    Weights for the maintenance priority score formula (contract §16).

    Formula:
        priority_score = (
            failure_risk    × evidence.failure_risk
          + criticality     × normalized(evidence.criticality)
          + mission_impact  × normalized(evidence.mission_impact)
          + urgency         × urgency_score
        )

    All weights MUST sum to 1.0.
    """

    failure_risk: float = 0.40
    criticality: float = 0.25
    mission_impact: float = 0.20
    urgency: float = 0.15

    def __post_init__(self) -> None:
        total = (
            self.failure_risk
            + self.criticality
            + self.mission_impact
            + self.urgency
        )
        if abs(total - 1.0) > 1e-9:
            raise ValueError(
                f"MaintenanceWeights must sum to 1.0, got {total}. "
                "Adjust weights before changing them."
            )


@dataclass(frozen=True)
class MaintenanceConfig:
    """Top-level maintenance priority configuration bundle."""

    weights: MaintenanceWeights = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.weights is None:
            object.__setattr__(self, "weights", MaintenanceWeights())


# ---------------------------------------------------------------------------
# Normalization maps
#
# These convert categorical Literal enum values to their 0.0–1.0 numeric
# equivalents used by the scoring formulas. They are defined here so they
# live in the single config location (contract §15 / §16).
# ---------------------------------------------------------------------------

#: Severity/criticality/risk → float normalization (shared across formulas)
LEVEL_TO_FLOAT: dict[str, float] = {
    "NONE": 0.0,
    "LOW": 0.25,
    "MEDIUM": 0.60,
    "HIGH": 1.0,
}

#: Maintenance urgency normalization used by the maintenance priority engine.
#: Urgency is derived from how overdue/imminently-due maintenance is.
MAINTENANCE_STATUS_TO_URGENCY: dict[str, float] = {
    "OVERDUE": 1.0,
    "SCHEDULED": 0.4,
    "COMPLETED": 0.0,
}


# ---------------------------------------------------------------------------
# Module-level singletons — import these; do NOT instantiate elsewhere
# ---------------------------------------------------------------------------

#: Canonical readiness configuration singleton.
#: Import this anywhere you need weights, thresholds, or hard-rule values.
READINESS_CONFIG: ReadinessConfig = ReadinessConfig()

#: Canonical maintenance configuration singleton.
#: Import this anywhere you need maintenance priority weights.
MAINTENANCE_CONFIG: MaintenanceConfig = MaintenanceConfig()
