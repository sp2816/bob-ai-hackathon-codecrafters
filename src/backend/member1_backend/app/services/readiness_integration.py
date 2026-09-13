import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from datetime import datetime

# ── Add backend folder and member2 folder to Python path ──
_BACKEND_PATH = Path(__file__).resolve().parents[3]
if str(_BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(_BACKEND_PATH))
    
_MEMBER2_PATH = _BACKEND_PATH / "member2_ml"
if str(_MEMBER2_PATH) not in sys.path:
    sys.path.insert(0, str(_MEMBER2_PATH))

from member2_ml.services.prediction_service import ComponentPredictionResult
from member3_readiness.evidence.models import ComponentInfo, MaintenanceInfo, EvidenceObject
from member3_readiness.missions.models import MissionInfo
from member3_readiness.services.readiness_service import ReadinessService

from app.models.asset import Asset
from app.models.component import Component
from app.models.maintenance_record import MaintenanceRecord
from app.models.prediction import Prediction
from app.models.anomaly import Anomaly
from app.models.mission import Mission
from app.models.readiness_result import ReadinessResult
from app.models.maintenance_recommendation import MaintenanceRecommendation

def run_readiness_pipeline(db: Session) -> dict:
    """
    Run Member 3's Readiness and Maintenance Priority pipeline.
    
    1. Fetches data from Member 1's database.
    2. Constructs Member 3 input models.
    3. Calls ReadinessService for evaluation and ranking.
    4. Persists the output ReadinessResult and MaintenanceRecommendation objects.
    """
    assets = db.query(Asset).all()
    components = db.query(Component).all()
    maintenance_records = db.query(MaintenanceRecord).all()
    predictions = db.query(Prediction).all()
    anomalies = db.query(Anomaly).all()
    missions = db.query(Mission).all()

    # Build lookup dictionaries
    pred_map = {(p.asset_id, p.component_id): p for p in predictions}
    anom_map = {(a.asset_id, a.component_id): a for a in anomalies}
    maint_map = {(m.asset_id, m.component_id): m for m in maintenance_records}
    
    # component_id_map for Phase D
    component_id_map: Dict[Tuple[str, str], str] = {}
    
    all_evidence: List[EvidenceObject] = []
    
    for comp in components:
        key = (comp.asset_id, comp.component_type)
        if key in component_id_map:
            print(f"WARNING: Duplicate component type '{comp.component_type}' for asset '{comp.asset_id}'. Using the first one encountered.")
        else:
            component_id_map[key] = comp.component_id

        # Gather Prediction
        p = pred_map.get((comp.asset_id, comp.component_id))
        if not p:
            raise ValueError(f"Missing ML prediction for asset {comp.asset_id}, component {comp.component_id}")
            
        a = anom_map.get((comp.asset_id, comp.component_id))
        
        cpr = ComponentPredictionResult(
            prediction_id=p.prediction_id,
            asset_id=comp.asset_id,
            component_id=comp.component_id,
            failure_probability=p.failure_probability,
            risk_category=p.risk_category,
            anomaly_score=a.anomaly_score if a else 0.0,
            anomaly_status=a.anomaly_status if a else "NORMAL",
            anomaly_severity=a.anomaly_severity if a else "LOW",
            sensor=a.sensor if a else "NONE",
            timestamp=p.timestamp
        )

        # Gather ComponentInfo
        c_info = ComponentInfo(
            component_id=comp.component_id,
            asset_id=comp.asset_id,
            component_type=comp.component_type,
            criticality=comp.criticality
        )

        # Gather MaintenanceInfo
        m = maint_map.get((comp.asset_id, comp.component_id))
        if not m:
            raise ValueError(f"Missing maintenance record for asset {comp.asset_id}, component {comp.component_id}")
            
        # Verify hours_since_service explicitly
        hours_since_service = m.hours_since_service
        if hours_since_service is None:
            raise ValueError(
                f"Missing required maintenance field: 'hours_since_service' for component {comp.component_id}. "
                "EvidenceObject cannot be constructed without operational hours."
            )
            
        # Member 3 requires a proper datetime object for maintenance_date
        try:
            m_date = datetime.fromisoformat(m.maintenance_date)
        except ValueError:
            # fallback if it's just a date 'YYYY-MM-DD'
            m_date = datetime.strptime(m.maintenance_date, "%Y-%m-%d")

        m_info = MaintenanceInfo(
            maintenance_id=m.maintenance_id,
            asset_id=m.asset_id,
            component_id=m.component_id,
            maintenance_type=m.maintenance_type,
            maintenance_date=m_date,
            status=m.status,
            hours_since_service=hours_since_service,
            technician_action=m.technician_action,
            notes=m.notes
        )
        
        # Build Evidence
        evidence = ReadinessService.build_component_evidence(cpr, c_info, m_info)
        all_evidence.append(evidence)

    # Convert missions
    mission_infos = []
    for m in missions:
        req_comps = json.loads(m.required_components) if m.required_components else []
        try:
            m_time = datetime.fromisoformat(m.scheduled_time)
        except ValueError:
            m_time = datetime.strptime(m.scheduled_time, "%Y-%m-%dT%H:%M:%S")

        m_info = MissionInfo(
            mission_id=m.mission_id,
            mission_name=m.mission_name,
            mission_type=m.mission_type,
            criticality=m.criticality,
            scheduled_time=m_time,
            required_components=req_comps,
            readiness_threshold=m.readiness_threshold
        )
        mission_infos.append(m_info)

    # Group evidence by asset_id
    evidence_by_asset: Dict[str, List[EvidenceObject]] = {}
    for ev in all_evidence:
        if ev.asset_id not in evidence_by_asset:
            evidence_by_asset[ev.asset_id] = []
        evidence_by_asset[ev.asset_id].append(ev)

    # Evaluate Readiness
    generated_readiness = 0
    # Generic readiness
    for asset_id, asset_evidence in evidence_by_asset.items():
        res = ReadinessService.evaluate_asset_readiness(asset_evidence)
        _persist_readiness(db, res)
        generated_readiness += 1
        
    # Mission readiness
    for m_info in mission_infos:
        for asset_id, asset_evidence in evidence_by_asset.items():
            res = ReadinessService.evaluate_mission_readiness(asset_evidence, m_info)
            _persist_readiness(db, res)
            generated_readiness += 1

    # Evaluate Maintenance Priorities
    generated_recommendations = 0
    recommendations = ReadinessService.rank_maintenance_actions(all_evidence, component_id_map)
    for rec in recommendations:
        _persist_recommendation(db, rec)
        generated_recommendations += 1

    db.commit()

    return {
        "readiness_results_generated": generated_readiness,
        "maintenance_recommendations_generated": generated_recommendations
    }

def _persist_readiness(db: Session, res) -> None:
    # res is member3_readiness.readiness.models.ReadinessResult
    # generate a unique ID based on asset and mission
    m_str = res.mission_id if res.mission_id else "GENERIC"
    rid = f"RDY-{res.asset_id}-{m_str}"
    
    existing = db.query(ReadinessResult).filter_by(result_id=rid).first()
    if existing:
        existing.readiness_score = res.readiness_score
        existing.readiness_status = res.readiness_status
        existing.reasons = json.dumps(res.reasons)
        existing.evidence = json.dumps([e.model_dump() for e in res.evidence])
        existing.timestamp = res.timestamp
    else:
        db.add(ReadinessResult(
            result_id=rid,
            asset_id=res.asset_id,
            mission_id=res.mission_id,
            readiness_score=res.readiness_score,
            readiness_status=res.readiness_status,
            reasons=json.dumps(res.reasons),
            evidence=json.dumps([e.model_dump() for e in res.evidence]),
            timestamp=res.timestamp
        ))
        
def _persist_recommendation(db: Session, rec) -> None:
    # rec is member3_readiness.maintenance.models.MaintenanceRecommendation
    # Note: Phase H - priority_score and component (string) are dropped here because they do not exist in Member 1's DB model.
    existing = db.query(MaintenanceRecommendation).filter_by(recommendation_id=rec.recommendation_id).first()
    if existing:
        existing.priority = rec.priority
        existing.action = rec.action
        existing.reason = rec.reason
        existing.risk = rec.risk
        existing.mission_impact = rec.mission_impact
        existing.urgency = rec.urgency
        existing.status = rec.status
    else:
        db.add(MaintenanceRecommendation(
            recommendation_id=rec.recommendation_id,
            asset_id=rec.asset_id,
            component_id=rec.component_id,
            priority=rec.priority,
            action=rec.action,
            reason=rec.reason,
            risk=rec.risk,
            mission_impact=rec.mission_impact,
            urgency=rec.urgency,
            status=rec.status
        ))
