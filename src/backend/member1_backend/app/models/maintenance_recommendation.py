from sqlalchemy import Column, String, Float, Integer, Text, JSON
from app.database import Base


class MaintenanceRecommendation(Base):
    """
    Stores maintenance recommendations written by Member 3's maintenance_optimizer.
    Member 1 owns the table definition; Member 3 populates it.
    """
    __tablename__ = "maintenance_recommendations"

    recommendation_id = Column(String, primary_key=True, index=True)
    asset_id = Column(String, nullable=False, index=True)
    component_id = Column(String, nullable=False, index=True)
    priority = Column(Integer, nullable=False)               # 1 = highest
    action = Column(String, nullable=False)
    reason = Column(Text, nullable=True)
    risk = Column(String, nullable=False)                    # LOW | MEDIUM | HIGH
    mission_impact = Column(String, nullable=False)          # LOW | MEDIUM | HIGH
    urgency = Column(String, nullable=False)                 # LOW | MEDIUM | HIGH
    status = Column(String, nullable=False, default="OPEN")  # OPEN | IN_PROGRESS | RESOLVED

    # --- New Expansion Fields ---
    decision = Column(String, nullable=True)                 # MONITOR | INSPECT_FIRST | REPAIR | REPLACE
    economic_impact = Column(JSON, nullable=True)            # Nested counterfactual economic model
    timeline = Column(JSON, nullable=True)                   # Dynamically generated chronological timeline steps
