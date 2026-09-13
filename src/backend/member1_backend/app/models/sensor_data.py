from sqlalchemy import Column, String, Float
from app.database import Base


class SensorData(Base):
    __tablename__ = "sensor_data"

    sensor_id = Column(String, primary_key=True, index=True)
    asset_id = Column(String, nullable=False, index=True)
    component_id = Column(String, nullable=False, index=True)
    timestamp = Column(String, nullable=False)          # ISO datetime string
    sensor_type = Column(String, nullable=False)        # vibration | temperature | pressure | RPM
    value = Column(Float, nullable=False)
