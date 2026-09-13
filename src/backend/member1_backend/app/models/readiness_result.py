from sqlalchemy import Column, String, Float, Text
from app.database import Base


class ReadinessResult(Base):
    """
    Stores computed readiness results written by Member 3's readiness_engine.
    Member 1 owns the table definition; Member 3 populates it.
    """
    __tablename__ = "readiness_results"

    result_id = Column(String, primary_key=True, index=True)
    asset_id = Column(String, nullable=False, index=True)
    mission_id = Column(String, nullable=True, index=True)  # null = generic readiness
    readiness_score = Column(Float, nullable=False)
    readiness_status = Column(String, nullable=False)        # READY | CONDITIONALLY_READY | NOT_READY
    reasons = Column(Text, nullable=True)                    # JSON-encoded list of reason strings
    evidence = Column(Text, nullable=True)                   # JSON-encoded Evidence object
    timestamp = Column(String, nullable=False)               # ISO datetime string
