from sqlalchemy import Column, String, Float, Date
from app.database import Base


class Component(Base):
    __tablename__ = "components"

    component_id = Column(String, primary_key=True, index=True)
    asset_id = Column(String, nullable=False, index=True)
    component_type = Column(String, nullable=False)
    criticality = Column(String, nullable=False)        # LOW | MEDIUM | HIGH
    installation_date = Column(String, nullable=True)   # ISO date string
    operating_hours = Column(Float, nullable=False, default=0.0)
    life_limit = Column(Float, nullable=True)
