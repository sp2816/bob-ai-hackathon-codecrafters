from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.asset import AssetResponse
from app.schemas.asset_create import AssetCreateRequest, AssetCreateResponse
from app.services import asset_service

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("/", response_model=List[AssetResponse])
def list_assets(db: Session = Depends(get_db)):
    return asset_service.get_all_assets(db)


@router.get("/{asset_id}", response_model=AssetResponse)
def get_asset(asset_id: str, db: Session = Depends(get_db)):
    asset = asset_service.get_asset_by_id(db, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.post("/", response_model=AssetCreateResponse, status_code=201)
def create_asset(request: AssetCreateRequest, db: Session = Depends(get_db)):
    """
    Add a new asset and run the full analysis pipeline:
        Asset/Component/Maintenance → SQLite
        Single-component ML inference (RF + IF)
        Evidence Layer → Readiness Engine → Maintenance Priority
        Returns complete analysis results.

    No fleet-wide rerun. Uses single-component inference only.
    """
    from app.services.asset_intake_service import create_asset_and_analyze
    try:
        return create_asset_and_analyze(db, request)
    except ValueError as e:
        msg = str(e)
        # Duplicate ID → 409 Conflict
        if "already exists" in msg:
            raise HTTPException(status_code=409, detail=msg)
        raise HTTPException(status_code=422, detail=msg)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=f"ML pipeline error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {e}")
