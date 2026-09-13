from sqlalchemy import Column, String, Float
from app.database import Base


class Anomaly(Base):
    """
    Stores Isolation Forest anomaly detection results written by Member 2.
    Member 1 owns the table definition; Member 2 populates it.

    Contract §8 — Isolation Forest output fields (exact names):
        asset_id, component_id, anomaly_score, anomaly_status,
        anomaly_severity, sensor, timestamp

    anomaly_id is a surrogate primary key — the contract defines no PK
    for Isolation Forest output, so Member 1 adds one for storage.
    """
    __tablename__ = "anomalies"

    anomaly_id = Column(String, primary_key=True, index=True)
    asset_id = Column(String, nullable=False, index=True)
    component_id = Column(String, nullable=False, index=True)
    anomaly_score = Column(Float, nullable=False)
    anomaly_status = Column(String, nullable=False)     # NORMAL | HIGH
    anomaly_severity = Column(String, nullable=False)   # LOW | MEDIUM | HIGH
    sensor = Column(String, nullable=False)             # vibration | temperature | pressure | RPM
    timestamp = Column(String, nullable=False)          # ISO datetime string
