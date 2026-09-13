from sqlalchemy import Column, String, Float, Text
from app.database import Base


class Mission(Base):
    __tablename__ = "missions"

    mission_id = Column(String, primary_key=True, index=True)
    mission_name = Column(String, nullable=False)
    mission_type = Column(String, nullable=False)
    criticality = Column(String, nullable=False)        # LOW | MEDIUM | HIGH
    scheduled_time = Column(String, nullable=True)      # ISO datetime string
    required_components = Column(Text, nullable=True)   # JSON-encoded list of component types
    readiness_threshold = Column(Float, nullable=False, default=0.66)
