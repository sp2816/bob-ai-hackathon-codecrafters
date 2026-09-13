"""
AssetSentinel — Member 3 Test Fixtures
src/backend/member3_readiness/tests/conftest.py

Provides deterministic pytest fixtures for all Member 3 tests.

Fixture strategy:
    - All fixtures are deterministic (no random values).
    - AS-1047 canonical demo scenario is represented as a fixture for testing
      purposes only. Production code MUST NOT reference AS-1047 by name.
    - Fixtures produce the SAME result on every run.
    - No real ML inference is performed — ComponentPredictionResult instances
      are constructed directly from the dataclass.

Member 2 dependency:
    ComponentPredictionResult is imported from Member 2 via the sys.path
    manipulation in builder.py. Here we import it the same way for
    fixture construction. No ML models are loaded in tests.
"""

from __future__ import annotations

import sys
import os
from datetime import datetime, timezone

import pytest

# ---------------------------------------------------------------------------
# Ensure member2_ml is on sys.path so ComponentPredictionResult is importable
# ---------------------------------------------------------------------------
_MEMBER2_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "member2_ml")
)
if _MEMBER2_PATH not in sys.path:
    sys.path.insert(0, _MEMBER2_PATH)

from services.prediction_service import ComponentPredictionResult  # noqa: E402

from member3_readiness.evidence.models import ComponentInfo, MaintenanceInfo  # noqa: E402


# ---------------------------------------------------------------------------
# Shared timestamp
# ---------------------------------------------------------------------------

FIXED_TIMESTAMP = datetime(2026, 9, 27, 12, 0, 0, tzinfo=timezone.utc).isoformat()


# ===========================================================================
# AS-1047 canonical demo fixtures
# (test-only — do NOT use asset_id conditionals in production code)
# ===========================================================================

@pytest.fixture
def as1047_prediction() -> ComponentPredictionResult:
    """
    AS-1047 main bearing — high failure probability, HIGH anomaly.
    Values reflect the canonical demo scenario (contract §23).
    The actual ML model produces these values; here we use them as
    deterministic test inputs.
    """
    return ComponentPredictionResult(
        prediction_id="PRED-TEST-AS1047-BRG",
        asset_id="AS-1047",
        component_id="BRG-1047",
        failure_probability=0.87,
        risk_category="HIGH",
        anomaly_score=-0.52,
        anomaly_status="HIGH",
        anomaly_severity="HIGH",
        sensor="vibration",
        timestamp=FIXED_TIMESTAMP,
    )


@pytest.fixture
def as1047_component_info() -> ComponentInfo:
    """AS-1047 main bearing component metadata."""
    return ComponentInfo(
        component_id="BRG-1047",
        asset_id="AS-1047",
        component_type="main_bearing",
        criticality="HIGH",
    )


@pytest.fixture
def as1047_maintenance_overdue() -> MaintenanceInfo:
    """
    AS-1047 main bearing maintenance record — OVERDUE.
    420 hours since last service; interval is 300 hours.
    """
    return MaintenanceInfo(
        maintenance_id="MNT-0002",
        asset_id="AS-1047",
        component_id="BRG-1047",
        maintenance_type="INSPECTION",
        maintenance_date=datetime(2026, 9, 27, tzinfo=timezone.utc),
        status="OVERDUE",
        hours_since_service=420.0,
        technician_action="Inspection OVERDUE by 120h. Immediate action required.",
        notes="Record created at 2450 operational hours.",
    )


# ===========================================================================
# Healthy asset fixtures (for READY / CONDITIONALLY_READY paths)
# ===========================================================================

@pytest.fixture
def healthy_prediction() -> ComponentPredictionResult:
    """A component with low failure probability and no anomaly."""
    return ComponentPredictionResult(
        prediction_id="PRED-TEST-HEALTHY",
        asset_id="AS-1001",
        component_id="BRG-1001",
        failure_probability=0.08,
        risk_category="LOW",
        anomaly_score=0.15,
        anomaly_status="NORMAL",
        anomaly_severity="LOW",
        sensor="NONE",
        timestamp=FIXED_TIMESTAMP,
    )


@pytest.fixture
def healthy_component_info() -> ComponentInfo:
    return ComponentInfo(
        component_id="BRG-1001",
        asset_id="AS-1001",
        component_type="main_bearing",
        criticality="HIGH",
    )


@pytest.fixture
def healthy_maintenance_current() -> MaintenanceInfo:
    return MaintenanceInfo(
        maintenance_id="MNT-0007",
        asset_id="AS-1001",
        component_id="BRG-1001",
        maintenance_type="INSPECTION",
        maintenance_date=datetime(2026, 1, 16, tzinfo=timezone.utc),
        status="COMPLETED",
        hours_since_service=120.0,
        notes="Completed at 860 operational hours.",
    )


# ===========================================================================
# Medium-risk fixtures (for CONDITIONALLY_READY path)
# ===========================================================================

@pytest.fixture
def medium_prediction() -> ComponentPredictionResult:
    return ComponentPredictionResult(
        prediction_id="PRED-TEST-MEDIUM",
        asset_id="AS-1002",
        component_id="ENG-1002",
        failure_probability=0.50,
        risk_category="MEDIUM",
        anomaly_score=-0.18,
        anomaly_status="HIGH",
        anomaly_severity="MEDIUM",
        sensor="temperature",
        timestamp=FIXED_TIMESTAMP,
    )


@pytest.fixture
def medium_component_info() -> ComponentInfo:
    return ComponentInfo(
        component_id="ENG-1002",
        asset_id="AS-1002",
        component_type="engine",
        criticality="MEDIUM",
    )


@pytest.fixture
def medium_maintenance_scheduled() -> MaintenanceInfo:
    return MaintenanceInfo(
        maintenance_id="MNT-MEDIUM-001",
        asset_id="AS-1002",
        component_id="ENG-1002",
        maintenance_type="INSPECTION",
        maintenance_date=datetime(2026, 9, 27, tzinfo=timezone.utc),
        status="SCHEDULED",
        hours_since_service=80.0,
    )


# ===========================================================================
# Multi-component fixtures for AS-1047 (engine + hydraulics)
# ===========================================================================

@pytest.fixture
def as1047_engine_prediction() -> ComponentPredictionResult:
    return ComponentPredictionResult(
        prediction_id="PRED-TEST-AS1047-ENG",
        asset_id="AS-1047",
        component_id="ENG-1047",
        failure_probability=0.22,
        risk_category="LOW",
        anomaly_score=0.05,
        anomaly_status="NORMAL",
        anomaly_severity="LOW",
        sensor="NONE",
        timestamp=FIXED_TIMESTAMP,
    )


@pytest.fixture
def as1047_engine_component_info() -> ComponentInfo:
    return ComponentInfo(
        component_id="ENG-1047",
        asset_id="AS-1047",
        component_type="engine",
        criticality="HIGH",
    )


@pytest.fixture
def as1047_engine_maintenance() -> MaintenanceInfo:
    return MaintenanceInfo(
        maintenance_id="MNT-0004",
        asset_id="AS-1047",
        component_id="ENG-1047",
        maintenance_type="INSPECTION",
        maintenance_date=datetime(2026, 9, 27, tzinfo=timezone.utc),
        status="SCHEDULED",
        hours_since_service=250.0,
    )
