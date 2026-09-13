from sqlalchemy.orm import Session
from app.models.asset import Asset
from app.schemas.asset import AssetCreate


def get_all_assets(db: Session):
    return db.query(Asset).all()


def get_asset_by_id(db: Session, asset_id: str):
    return db.query(Asset).filter(Asset.asset_id == asset_id).first()


def create_asset(db: Session, asset: AssetCreate):
    db_asset = Asset(**asset.model_dump())
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset
