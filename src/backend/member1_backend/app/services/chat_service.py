"""
AssetSentinel — Real IBM AI Chat Service
src/backend/member1_backend/app/services/chat_service.py

This service has been completely refactored to remove all mock, regex, and 
hardcoded intent matching. It now delegates entirely to the genuine IBM Watsonx.ai
integration in `watsonx_service.py`.
"""

from sqlalchemy.orm import Session
from app.services.watsonx_service import process_message_with_watsonx

def process_chat_message(message: str, db: Session) -> str:
    """
    Process the incoming chat message by delegating to the Real IBM AI (Watsonx).
    The 'db' parameter is no longer directly needed here since Watsonx tool calls
    manage their own DB sessions, but we keep the signature for backwards compatibility
    with the chat.py router.
    """
    return process_message_with_watsonx(message)
