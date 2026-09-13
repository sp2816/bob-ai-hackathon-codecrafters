from pydantic import BaseModel


class PredictionBase(BaseModel):
    prediction_id: str
    asset_id: str
    component_id: str
    failure_probability: float
    risk_category: str              # LOW | MEDIUM | HIGH
    timestamp: str                  # ISO datetime string


class PredictionCreate(PredictionBase):
    pass


class PredictionResponse(PredictionBase):
    model_config = {"from_attributes": True}
