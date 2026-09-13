from pydantic import BaseModel


class AnomalyBase(BaseModel):
    """
    Pydantic schema for Isolation Forest anomaly output.

    Contract §8 — exact field names:
        asset_id, component_id, anomaly_score, anomaly_status,
        anomaly_severity, sensor, timestamp

    Allowed anomaly_status  : NORMAL | HIGH
    Allowed anomaly_severity: LOW | MEDIUM | HIGH
    """
    anomaly_id: str
    asset_id: str
    component_id: str
    anomaly_score: float
    anomaly_status: str         # NORMAL | HIGH
    anomaly_severity: str       # LOW | MEDIUM | HIGH
    sensor: str                 # vibration | temperature | pressure | RPM
    timestamp: str              # ISO datetime string


class AnomalyCreate(AnomalyBase):
    pass


class AnomalyResponse(AnomalyBase):
    model_config = {"from_attributes": True}
