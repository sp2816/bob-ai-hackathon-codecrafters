"""
AssetSentinel — Evidence Layer: Builder
Member 3 (Tisha) | src/backend/member3_readiness/evidence/builder.py

Purpose:
    Assembles canonical EvidenceObject instances from:
        A. Member 2 ML output (ComponentPredictionResult)
        B. ComponentInfo  — component metadata (component_type, criticality)
        C. MaintenanceInfo — maintenance record + hours_since_service
        D. mission_impact  — explicit typed value (default "NONE")

    Two public functions are provided:

        build_evidence(prediction, component_info, maintenance_info, mission_impact)
            → EvidenceObject
            Single-component evidence assembly.

        build_evidence_for_asset(predictions, component_info_list, maintenance_info_list, mission_impact)
            → list[EvidenceObject]
            Multi-component evidence assembly from ONE already-generated
            prediction list. Does NOT call predict_all_components() internally.

ML → Evidence field mapping (contract §20):
    failure_probability   → failure_risk        (same numeric value; Member 3 owns the name)
    risk_category         → risk_level          (same enum value)
    sensor                → anomaly.sensor
    anomaly_severity      → anomaly.severity
    maintenance.status    → maintenance.inspection_status
    maintenance.hours_since_service → maintenance.hours_since_service
    component.criticality → criticality
    (explicit param)      → mission_impact

Fields intentionally NOT forwarded to EvidenceObject:
    anomaly_status   — NORMAL/HIGH; stays in upstream ML output only
    anomaly_score    — raw float; not part of contract §9/10 EvidenceObject
    prediction_id    — ML identifier; not part of EvidenceObject
    component_id     — kept in adapter context only (contract §10 uses "component")

Architecture:
    Member 3 → consumes Member 2 output (one-directional dependency).
    Member 2 must NOT import Member 3.
    This module does NOT call predict_all_components() or run inference.
    Callers provide an already-generated prediction list.

Ownership:
    - Only Member 3 modifies this file.
    - Do NOT add readiness/mission/maintenance-priority logic here.
"""

from __future__ import annotations

import sys
import os
from typing import Optional

# ---------------------------------------------------------------------------
# Import Member 2's ComponentPredictionResult.
#
# Member 2's services/prediction_service.py uses relative imports:
#     from features.feature_engineering import ...
#     from models.model_utils import ...
#
# To make these resolve without modifying Member 2 code, we add
# member2_ml to sys.path when it isn't already present.
# This is the cleanest approach given the current repository layout
# (no top-level pyproject.toml or shared virtualenv).
#
# Integration note: When Member 1 creates a shared FastAPI app that
# runs from a configured PYTHONPATH, this sys.path manipulation will
# become unnecessary and can be removed.
# ---------------------------------------------------------------------------

_MEMBER2_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "member2_ml")
)
if _MEMBER2_PATH not in sys.path:
    sys.path.insert(0, _MEMBER2_PATH)

from services.prediction_service import ComponentPredictionResult  # noqa: E402

# ---------------------------------------------------------------------------
# Member 3 models
# ---------------------------------------------------------------------------
from .models import (  # noqa: E402
    AnomalyEvidence,
    ComponentInfo,
    EvidenceObject,
    MaintenanceEvidence,
    MaintenanceInfo,
    MissionImpactLevel,
)


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

class EvidenceAssemblyError(ValueError):
    """
    Raised when evidence cannot be assembled due to inconsistent or invalid inputs.
    Callers must handle this rather than silently receiving partial evidence.
    """


def _validate_asset_match(prediction: ComponentPredictionResult, component: ComponentInfo) -> None:
    """Ensure prediction and component refer to the same asset."""
    if prediction.asset_id != component.asset_id:
        raise EvidenceAssemblyError(
            f"asset_id mismatch: prediction has '{prediction.asset_id}', "
            f"component has '{component.asset_id}'. "
            "All inputs must refer to the same asset."
        )


def _validate_component_match(
    prediction: ComponentPredictionResult, component: ComponentInfo
) -> None:
    """Ensure prediction and component refer to the same component."""
    if prediction.component_id != component.component_id:
        raise EvidenceAssemblyError(
            f"component_id mismatch: prediction has '{prediction.component_id}', "
            f"component_info has '{component.component_id}'."
        )


def _validate_maintenance_match(
    prediction: ComponentPredictionResult, maintenance: MaintenanceInfo
) -> None:
    """Ensure prediction asset and maintenance asset/component refer to the same records."""
    if prediction.asset_id != maintenance.asset_id:
        raise EvidenceAssemblyError(
            f"asset_id mismatch between prediction ('{prediction.asset_id}') "
            f"and maintenance record ('{maintenance.asset_id}')."
        )
    if prediction.component_id != maintenance.component_id:
        raise EvidenceAssemblyError(
            f"component_id mismatch between prediction ('{prediction.component_id}') "
            f"and maintenance record ('{maintenance.component_id}')."
        )


def _validate_failure_probability(prob: float) -> None:
    """Explicit guard for the failure_probability range."""
    if not isinstance(prob, (int, float)):
        raise EvidenceAssemblyError(
            f"failure_probability must be a float, got {type(prob).__name__}."
        )
    if not (0.0 <= float(prob) <= 1.0):
        raise EvidenceAssemblyError(
            f"failure_probability must be in [0.0, 1.0], got {prob}. "
            "This is NOT RUL — it is a failure risk probability."
        )


# ---------------------------------------------------------------------------
# Core mapping: ComponentPredictionResult → Evidence sub-objects
# ---------------------------------------------------------------------------

def _map_anomaly_evidence(prediction: ComponentPredictionResult) -> AnomalyEvidence:
    """
    Map Member 2's anomaly fields to the canonical AnomalyEvidence sub-object.

    Mapping (contract §20):
        prediction.sensor           → anomaly.sensor
        prediction.anomaly_severity → anomaly.severity

    anomaly_status (NORMAL/HIGH) is NOT forwarded — it is an upstream ML
    classification field, not part of the EvidenceObject contract (§9/10).
    """
    return AnomalyEvidence(
        sensor=prediction.sensor,
        severity=prediction.anomaly_severity,
    )


def _map_maintenance_evidence(maintenance: MaintenanceInfo) -> MaintenanceEvidence:
    """
    Map MaintenanceInfo to the canonical MaintenanceEvidence sub-object.

    Mapping (contract §10):
        maintenance.hours_since_service → maintenance.hours_since_service
        maintenance.status              → maintenance.inspection_status
    """
    return MaintenanceEvidence(
        hours_since_service=maintenance.hours_since_service,
        inspection_status=maintenance.status,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_evidence(
    prediction: ComponentPredictionResult,
    component_info: ComponentInfo,
    maintenance_info: MaintenanceInfo,
    mission_impact: MissionImpactLevel = "NONE",
) -> EvidenceObject:
    """
    Assemble a canonical EvidenceObject for a single component.

    Args:
        prediction:      ComponentPredictionResult from Member 2's ML service.
                         Must be pre-fetched by the caller — this function
                         does NOT call predict_all_components().
        component_info:  Typed component metadata (component_type, criticality).
                         Provides the 'component' field and criticality.
        maintenance_info: Typed maintenance record including hours_since_service.
        mission_impact:  Mission-specific impact level (default "NONE" for
                         generic / non-mission-specific evidence).

    Returns:
        EvidenceObject   Canonical evidence ready for the Readiness Engine.

    Raises:
        EvidenceAssemblyError  If any identifier mismatch or invalid value is detected.
        pydantic.ValidationError  If Pydantic type constraints are violated.

    Contract alignment:
        failure_probability  → failure_risk   (same value; Member 3 owns name)
        risk_category        → risk_level     (same enum value)
        sensor               → anomaly.sensor
        anomaly_severity     → anomaly.severity
        maintenance.status   → maintenance.inspection_status
        component_type       → component      (display name, NOT component_id)
    """
    # --- Validation ---
    _validate_failure_probability(prediction.failure_probability)
    _validate_asset_match(prediction, component_info)
    _validate_component_match(prediction, component_info)
    _validate_maintenance_match(prediction, maintenance_info)

    # --- Assemble sub-objects ---
    anomaly = _map_anomaly_evidence(prediction)
    maintenance = _map_maintenance_evidence(maintenance_info)

    # --- Build canonical EvidenceObject ---
    # component_id is intentionally NOT included (contract §10 uses "component").
    return EvidenceObject(
        asset_id=prediction.asset_id,
        component=component_info.component_type,
        failure_risk=prediction.failure_probability,  # numeric value preserved exactly
        risk_level=prediction.risk_category,          # enum value preserved exactly
        anomaly=anomaly,
        maintenance=maintenance,
        criticality=component_info.criticality,
        mission_impact=mission_impact,
    )


def build_evidence_for_asset(
    predictions: list[ComponentPredictionResult],
    component_info_list: list[ComponentInfo],
    maintenance_info_list: list[MaintenanceInfo],
    mission_impact: MissionImpactLevel = "NONE",
) -> list[EvidenceObject]:
    """
    Assemble EvidenceObject instances for multiple components of one asset
    from a SINGLE pre-fetched prediction list.

    This function must be called with an already-generated predictions list
    (e.g. the output of predict_all_components() called ONCE by the caller).
    It does NOT call predict_all_components() internally to avoid repeated
    full-dataset inference.

    Matching strategy:
        For each ComponentInfo in component_info_list, find the corresponding
        prediction and maintenance record by (asset_id, component_id).
        Components with no matching prediction are skipped with a warning.
        Components with no matching maintenance record raise EvidenceAssemblyError.

    Args:
        predictions:          Pre-fetched list[ComponentPredictionResult].
        component_info_list:  List of ComponentInfo for each component to process.
        maintenance_info_list: List of MaintenanceInfo for each component to process.
        mission_impact:       Mission impact level applied to all components equally.
                              Use "NONE" for generic fleet-wide evidence.

    Returns:
        list[EvidenceObject]  One EvidenceObject per successfully matched component.
                              Ordering matches component_info_list order.

    Raises:
        EvidenceAssemblyError  If a component has a matching prediction but no
                               matching maintenance record, or identifier mismatches.
        ValueError             If predictions or component_info_list are empty.
    """
    if not predictions:
        raise ValueError("predictions list must not be empty.")
    if not component_info_list:
        raise ValueError("component_info_list must not be empty.")

    # Build lookup indexes — O(n) build, O(1) lookup per component
    pred_index: dict[tuple[str, str], ComponentPredictionResult] = {
        (p.asset_id, p.component_id): p for p in predictions
    }
    maint_index: dict[tuple[str, str], MaintenanceInfo] = {
        (m.asset_id, m.component_id): m for m in maintenance_info_list
    }

    results: list[EvidenceObject] = []

    for comp in component_info_list:
        key = (comp.asset_id, comp.component_id)

        # Look up prediction for this component
        prediction = pred_index.get(key)
        if prediction is None:
            # No ML prediction available for this component — skip it.
            # This is expected when a component was not scored (e.g. missing
            # sensor data). Callers may inspect the returned list length.
            import warnings
            warnings.warn(
                f"No ML prediction found for component_id='{comp.component_id}' "
                f"of asset_id='{comp.asset_id}'. Skipping this component.",
                stacklevel=2,
            )
            continue

        # Look up maintenance record for this component
        maintenance = maint_index.get(key)
        if maintenance is None:
            raise EvidenceAssemblyError(
                f"No maintenance record found for component_id='{comp.component_id}' "
                f"of asset_id='{comp.asset_id}'. "
                "Maintenance information is required to assemble evidence."
            )

        # Assemble evidence for this component (re-uses single-component function)
        evidence = build_evidence(
            prediction=prediction,
            component_info=comp,
            maintenance_info=maintenance,
            mission_impact=mission_impact,
        )
        results.append(evidence)

    return results
