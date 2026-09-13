from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.asset import AssetResponse
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
