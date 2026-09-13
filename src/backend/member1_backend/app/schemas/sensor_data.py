from pydantic import BaseModel


class SensorDataBase(BaseModel):
    sensor_id: str
    asset_id: str
    component_id: str
    timestamp: str               # ISO datetime string
    sensor_type: str             # vibration | temperature | pressure | RPM
    value: float


class SensorDataCreate(SensorDataBase):
    pass


class SensorDataResponse(SensorDataBase):
    model_config = {"from_attributes": True}
