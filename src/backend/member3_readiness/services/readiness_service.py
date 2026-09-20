"""
AssetSentinel — Member 3 Public Facade
Member 3 (Tisha) | src/backend/member3_readiness/services/readiness_service.py

Purpose:
    Provides a clean, unified public interface for Member 1 (Unified Backend)
    to consume Member 3's functionalities without needing to understand the
    internal package structure (evidence, readiness, missions, maintenance).

    All business logic remains in the respective engines. This is strictly a facade.
"""

from typing import Optional

from member3_readiness.evidence.builder import build_evidence
from member3_readiness.evidence.models import ComponentInfo, EvidenceObject, MaintenanceInfo, MissionImpactLevel
from member3_readiness.maintenance.models import MaintenanceRecommendation
from member3_readiness.maintenance.priority_engine import rank_maintenance
from member3_readiness.missions.evaluator import evaluate_for_mission
from member3_readiness.missions.models import MissionInfo
from member3_readiness.readiness.engine import evaluate as evaluate_readiness
from member3_readiness.readiness.models import ReadinessResult
from member2_ml.services.prediction_service import ComponentPredictionResult

class ReadinessService:
    """
    Public API for Member 3 Readiness & Maintenance functionality.
    """

    @staticmethod
    def build_component_evidence(
        prediction: ComponentPredictionResult,
        component_info: ComponentInfo,
        maintenance_info: MaintenanceInfo,
        mission_impact: MissionImpactLevel = "NONE",
    ) -> EvidenceObject:
        """
        Build a canonical EvidenceObject from upstream data.
        
        This bridges Member 2's ML output and Member 1's DB records into the
        strict canonical format required by the Readiness Engine.
        """
        return build_evidence(
            prediction=prediction,
            component_info=component_info,
            maintenance_info=maintenance_info,
            mission_impact=mission_impact,
        )

    @staticmethod
    def evaluate_asset_readiness(
        evidence_list: list[EvidenceObject]
    ) -> ReadinessResult:
        """
        Evaluate generic readiness for an asset based on its components' evidence.
        """
        return evaluate_readiness(evidence_list=evidence_list)

    @staticmethod
    def evaluate_mission_readiness(
        evidence_list: list[EvidenceObject],
        mission: MissionInfo,
    ) -> ReadinessResult:
        """
        Evaluate asset readiness in the context of a specific mission.
        """
        return evaluate_for_mission(evidence_list=evidence_list, mission=mission)

    @staticmethod
    def rank_maintenance_actions(
        evidence_list: list[EvidenceObject],
        component_id_map: Optional[dict[tuple[str, str], str]] = None,
        cost_assumptions_map: Optional[dict[str, dict]] = None,
    ) -> list[MaintenanceRecommendation]:
        """
        Generate and rank maintenance recommendations across the fleet.
        
        Args:
            evidence_list: List of all components' evidence.
            component_id_map: Mapping of (asset_id, component_type) -> component_id.
                Required because EvidenceObject intentionally omits component_id by contract,
                but MaintenanceRecommendation explicitly requires it.
        """
        return rank_maintenance(
            evidence_list=evidence_list,
            component_id_map=component_id_map,
            cost_assumptions_map=cost_assumptions_map,
        )
