from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.component import ComponentResponse
from app.services import component_service

router = APIRouter(prefix="/components", tags=["components"])


@router.get("/{asset_id}", response_model=List[ComponentResponse])
def list_components_for_asset(asset_id: str, db: Session = Depends(get_db)):
    return component_service.get_components_by_asset(db, asset_id)


@router.get("/detail/{component_id}", response_model=ComponentResponse)
def get_component(component_id: str, db: Session = Depends(get_db)):
    component = component_service.get_component_by_id(db, component_id)
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
    return component
