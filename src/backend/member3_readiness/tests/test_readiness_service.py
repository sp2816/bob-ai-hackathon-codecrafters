"""
AssetSentinel — Member 3 Public Facade Tests
Member 3 (Tisha) | src/backend/member3_readiness/tests/test_readiness_service.py
"""

import pytest

from member3_readiness.services.readiness_service import ReadinessService
from member3_readiness.evidence.models import EvidenceObject, ComponentInfo, MaintenanceInfo
from member3_readiness.readiness.models import ReadinessResult
from member3_readiness.maintenance.models import MaintenanceRecommendation
from member3_readiness.missions.models import MissionInfo
from member2_ml.services.prediction_service import ComponentPredictionResult
from datetime import datetime, timezone

@pytest.fixture
def sample_prediction():
    return ComponentPredictionResult(
        prediction_id="PRED-123",
        asset_id="AS-1047",
        component_id="BRG-1047",
        failure_probability=0.87,
        risk_category="HIGH",
        anomaly_score=0.9,
        anomaly_status="HIGH",
        anomaly_severity="HIGH",
        sensor="vibration",
        timestamp=datetime(2026, 1, 16, tzinfo=timezone.utc),
    )

@pytest.fixture
def sample_component():
    return ComponentInfo(
        component_id="BRG-1047",
        asset_id="AS-1047",
        component_type="main_bearing",
        criticality="HIGH",
    )

@pytest.fixture
def sample_maintenance():
    return MaintenanceInfo(
        maintenance_id="MNT-123",
        asset_id="AS-1047",
        component_id="BRG-1047",
        maintenance_type="INSPECTION",
        maintenance_date=datetime(2025, 12, 1, tzinfo=timezone.utc),
        status="OVERDUE",
        hours_since_service=500.0,
    )

class TestReadinessService:
    def test_build_component_evidence(self, sample_prediction, sample_component, sample_maintenance):
        evidence = ReadinessService.build_component_evidence(
            prediction=sample_prediction,
            component_info=sample_component,
            maintenance_info=sample_maintenance,
        )
        assert isinstance(evidence, EvidenceObject)
        assert evidence.asset_id == "AS-1047"
        assert evidence.component == "main_bearing"
        assert evidence.failure_risk == 0.87

    def test_evaluate_asset_readiness(self, sample_prediction, sample_component, sample_maintenance):
        evidence = ReadinessService.build_component_evidence(
            prediction=sample_prediction,
            component_info=sample_component,
            maintenance_info=sample_maintenance,
        )
        result = ReadinessService.evaluate_asset_readiness([evidence])
        assert isinstance(result, ReadinessResult)
        assert result.readiness_status == "NOT_READY"

    def test_evaluate_mission_readiness(self, sample_prediction, sample_component, sample_maintenance):
        evidence = ReadinessService.build_component_evidence(
            prediction=sample_prediction,
            component_info=sample_component,
            maintenance_info=sample_maintenance,
        )
        mission = MissionInfo(
            mission_id="MSN-003",
            mission_name="Strike",
            mission_type="COMBAT",
            criticality="HIGH",
            scheduled_time=datetime(2026, 1, 20, tzinfo=timezone.utc),
            required_components=["main_bearing"],
            readiness_threshold=0.35,
        )
        result = ReadinessService.evaluate_mission_readiness([evidence], mission)
        assert isinstance(result, ReadinessResult)
        assert result.mission_id == "MSN-003"

    def test_rank_maintenance_actions(self, sample_prediction, sample_component, sample_maintenance):
        evidence = ReadinessService.build_component_evidence(
            prediction=sample_prediction,
            component_info=sample_component,
            maintenance_info=sample_maintenance,
        )
        cid_map = {("AS-1047", "main_bearing"): "BRG-1047"}
        recommendations = ReadinessService.rank_maintenance_actions([evidence], component_id_map=cid_map)
        
        assert len(recommendations) == 1
        assert isinstance(recommendations[0], MaintenanceRecommendation)
        assert recommendations[0].component_id == "BRG-1047"
        assert recommendations[0].priority == 1
