import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.mission import Mission
from app.models.readiness_result import ReadinessResult
from app.schemas.mission import MissionResponse
from app.schemas.readiness_result import ReadinessResultResponse

router = APIRouter(prefix="/missions", tags=["missions"])


@router.get("/", response_model=List[MissionResponse])
def list_missions(db: Session = Depends(get_db)):
    missions = db.query(Mission).all()
    return [_serialize_mission(m) for m in missions]


@router.get("/{mission_id}", response_model=MissionResponse)
def get_mission(mission_id: str, db: Session = Depends(get_db)):
    mission = db.query(Mission).filter(Mission.mission_id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return _serialize_mission(mission)


@router.get("/{mission_id}/readiness", response_model=List[ReadinessResultResponse])
def get_mission_readiness(mission_id: str, db: Session = Depends(get_db)):
    """Return all readiness results computed for this mission (by Member 3)."""
    results = (
        db.query(ReadinessResult)
        .filter(ReadinessResult.mission_id == mission_id)
        .all()
    )
    return [_serialize_readiness(r) for r in results]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _serialize_mission(m: Mission) -> dict:
    """Deserialize JSON-encoded required_components back to a list."""
    return {
        "mission_id": m.mission_id,
        "mission_name": m.mission_name,
        "mission_type": m.mission_type,
        "criticality": m.criticality,
        "scheduled_time": m.scheduled_time,
        "required_components": json.loads(m.required_components) if m.required_components else None,
        "readiness_threshold": m.readiness_threshold,
    }


def _serialize_readiness(r: ReadinessResult) -> dict:
    return {
        "result_id": r.result_id,
        "asset_id": r.asset_id,
        "mission_id": r.mission_id,
        "readiness_score": r.readiness_score,
        "readiness_status": r.readiness_status,
        "reasons": json.loads(r.reasons) if r.reasons else None,
        "evidence": json.loads(r.evidence) if r.evidence else None,
        "timestamp": r.timestamp,
    }
