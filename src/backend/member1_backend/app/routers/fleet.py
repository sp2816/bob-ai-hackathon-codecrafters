import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.asset import Asset
from app.schemas.asset import AssetResponse

router = APIRouter(prefix="/fleet", tags=["fleet"])


@router.get("/", response_model=List[AssetResponse])
def fleet_overview(db: Session = Depends(get_db)):
    """Return all assets with their latest current_status and readiness_score."""
    return db.query(Asset).all()


@router.get("/readiness-summary")
def fleet_readiness_summary(db: Session = Depends(get_db)):
    """
    Aggregate readiness status counts across the fleet.
    Returns counts of READY, CONDITIONALLY_READY, NOT_READY assets.
    """
    assets = db.query(Asset).all()
    summary = {"READY": 0, "CONDITIONALLY_READY": 0, "NOT_READY": 0, "UNKNOWN": 0}
    for asset in assets:
        status = asset.current_status if asset.current_status in summary else "UNKNOWN"
        summary[status] += 1
    return {"total": len(assets), "counts": summary}


@router.post("/run-ml", tags=["fleet"])
def trigger_ml_pipeline(db: Session = Depends(get_db)):
    """
    Trigger Member 2's ML pipeline and store results in the DB.
    Call this after Member 2 pushes new code to refresh predictions + anomalies.
    """
    try:
        from app.services.ml_integration import run_ml_and_store
        summary = run_ml_and_store(db)
        return {"status": "ok", "stored": summary}
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

@router.post("/run-readiness", tags=["fleet"])
def trigger_readiness_pipeline(db: Session = Depends(get_db)):
    """
    Trigger Member 3's Readiness and Maintenance Priority pipeline.
    """
    try:
        from app.services.readiness_integration import run_readiness_pipeline
        summary = run_readiness_pipeline(db)
        return {"status": "ok", "generated": summary}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
