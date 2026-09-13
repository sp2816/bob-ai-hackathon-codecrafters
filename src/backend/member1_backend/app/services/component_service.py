from sqlalchemy.orm import Session
from app.models.component import Component
from app.schemas.component import ComponentCreate


def get_components_by_asset(db: Session, asset_id: str):
    return db.query(Component).filter(Component.asset_id == asset_id).all()


def get_component_by_id(db: Session, component_id: str):
    return db.query(Component).filter(Component.component_id == component_id).first()


def create_component(db: Session, component: ComponentCreate):
    db_component = Component(**component.model_dump())
    db.add(db_component)
    db.commit()
    db.refresh(db_component)
    return db_component
