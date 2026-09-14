from typing import Optional
from pydantic import BaseModel

class Notification(BaseModel):
    id: str
    title: str
    message: str
    severity: str
    source: str
    asset_id: Optional[str] = None
    timestamp: str

    class Config:
        from_attributes = True
