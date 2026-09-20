import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.asset import Asset
from app.models.maintenance_recommendation import MaintenanceRecommendation
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
        
    # Aggregate economic KPIs from MaintenanceRecommendations
    recs = db.query(MaintenanceRecommendation).all()
    
    fleet_traditional_cost = 0.0
    fleet_assetsentinel_cost = 0.0
    fleet_deployment_cost = 0.0
    
    for r in recs:
        if r.economic_impact:
            fleet_traditional_cost += r.economic_impact.get("traditional", {}).get("total", 0.0)
            fleet_assetsentinel_cost += r.economic_impact.get("assetsentinel", {}).get("total", 0.0)
            fleet_deployment_cost += r.economic_impact.get("deployment_cost", 0.0)
            
    fleet_potential_cost_avoided = fleet_traditional_cost - fleet_assetsentinel_cost
    fleet_net_economic_benefit = fleet_potential_cost_avoided - fleet_deployment_cost
    fleet_roi_percent = (fleet_net_economic_benefit / fleet_deployment_cost * 100) if fleet_deployment_cost > 0 else 0.0

    return {
        "total": len(assets), 
        "counts": summary,
        "economics": {
            "fleet_traditional_cost": fleet_traditional_cost,
            "fleet_assetsentinel_cost": fleet_assetsentinel_cost,
            "fleet_potential_cost_avoided": fleet_potential_cost_avoided,
            "fleet_deployment_cost": fleet_deployment_cost,
            "fleet_net_economic_benefit": fleet_net_economic_benefit,
            "fleet_roi_percent": fleet_roi_percent
        }
    }


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
