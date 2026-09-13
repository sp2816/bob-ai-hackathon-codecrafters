from sqlalchemy import Column, String, Float
from app.database import Base


class Prediction(Base):
    """
    Stores ML prediction results written by Member 2's prediction_engine.
    Member 1 owns the table definition; Member 2 populates it.
    """
    __tablename__ = "predictions"

    prediction_id = Column(String, primary_key=True, index=True)
    asset_id = Column(String, nullable=False, index=True)
    component_id = Column(String, nullable=False, index=True)
    failure_probability = Column(Float, nullable=False)
    risk_category = Column(String, nullable=False)      # LOW | MEDIUM | HIGH
    timestamp = Column(String, nullable=False)           # ISO datetime string
