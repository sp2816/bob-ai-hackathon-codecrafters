from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.cost_assumption import CostAssumption
from app.schemas.cost_assumption import CostAssumptionResponse, CostAssumptionCreate

router = APIRouter(prefix="/cost-assumptions", tags=["cost-assumptions"])

@router.get("/", response_model=List[CostAssumptionResponse])
def get_cost_assumptions(db: Session = Depends(get_db)):
    """Retrieve all configurable cost assumptions."""
    return db.query(CostAssumption).all()

@router.get("/{component_type}", response_model=CostAssumptionResponse)
def get_cost_assumption(component_type: str, db: Session = Depends(get_db)):
    """Retrieve cost assumptions for a specific component type."""
    assumption = db.query(CostAssumption).filter(CostAssumption.component_type == component_type).first()
    if not assumption:
        raise HTTPException(status_code=404, detail=f"Cost assumptions for {component_type} not found")
    return assumption

@router.put("/{component_type}", response_model=CostAssumptionResponse)
def update_cost_assumption(component_type: str, update_data: CostAssumptionCreate, db: Session = Depends(get_db)):
    """Update cost assumptions for a specific component type."""
    assumption = db.query(CostAssumption).filter(CostAssumption.component_type == component_type).first()
    if not assumption:
        raise HTTPException(status_code=404, detail=f"Cost assumptions for {component_type} not found")
    
    for key, value in update_data.model_dump().items():
        setattr(assumption, key, value)
        
    db.commit()
    db.refresh(assumption)
    return assumption
