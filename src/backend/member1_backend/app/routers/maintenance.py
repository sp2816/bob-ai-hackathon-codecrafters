from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.maintenance_record import MaintenanceRecordResponse
from app.schemas.maintenance_recommendation import MaintenanceRecommendationResponse
from app.schemas.cost_assumption import CostAssumptionResponse
from app.models.maintenance_recommendation import MaintenanceRecommendation
from app.models.cost_assumption import CostAssumption
from app.services import maintenance_service

router = APIRouter(prefix="/maintenance", tags=["maintenance"])


@router.get("/recommendations", response_model=List[MaintenanceRecommendationResponse])
def list_maintenance_recommendations(db: Session = Depends(get_db)):
    """Return all ranked maintenance recommendations."""
    return db.query(MaintenanceRecommendation).order_by(MaintenanceRecommendation.priority.asc()).all()


@router.get("/{asset_id}", response_model=List[MaintenanceRecordResponse])
def list_maintenance_for_asset(asset_id: str, db: Session = Depends(get_db)):
    return maintenance_service.get_maintenance_by_asset(db, asset_id)


@router.get("/component/{component_id}", response_model=List[MaintenanceRecordResponse])
def list_maintenance_for_component(component_id: str, db: Session = Depends(get_db)):
    return maintenance_service.get_maintenance_by_component(db, component_id)


@router.get("/timeline/{asset_id}")
def get_asset_timeline(asset_id: str, db: Session = Depends(get_db)):
    """Returns the dynamically generated timeline for an asset."""
    # To generate the timeline dynamically, we need the EvidenceObject, Decision, and Urgency.
    # Since rank_maintenance already computed it, we can just grab the top recommendation for the asset,
    # re-derive or just return the saved state. Actually, the Timeline Engine is stateless and we decided
    # to dynamically generate it. But we didn't persist it. Let's just generate it on the fly by calling
    # the readiness integration or just fetching the recommendation and reconstructing it.
    
    rec = db.query(MaintenanceRecommendation).filter_by(asset_id=asset_id).order_by(MaintenanceRecommendation.priority.asc()).first()
    if not rec:
        return {"timeline": []}
        
    from member3_readiness.maintenance.timeline_engine import build_timeline
    
    # We mock EvidenceObject parts needed for timeline: we just need decision and urgency!
    # build_timeline just needs: decision, urgency (EvidenceObject is barely used, we can pass None or a dummy)
    
    timeline = build_timeline(None, rec.decision or "MONITOR", rec.urgency)
    return {"timeline": timeline}
