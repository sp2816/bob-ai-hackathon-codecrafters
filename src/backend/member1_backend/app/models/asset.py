from sqlalchemy import Column, String, Float
from app.database import Base


class Asset(Base):
    __tablename__ = "assets"

    asset_id = Column(String, primary_key=True, index=True)
    asset_name = Column(String, nullable=False)
    asset_type = Column(String, nullable=False)
    unit = Column(String, nullable=False)
    operational_hours = Column(Float, nullable=False, default=0.0)
    current_status = Column(String, nullable=False, default="READY")
    readiness_score = Column(Float, nullable=True)
