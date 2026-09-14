from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.notification import Notification
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("/", response_model=List[Notification])
def get_notifications(db: Session = Depends(get_db)):
    return notification_service.get_all_notifications(db)
