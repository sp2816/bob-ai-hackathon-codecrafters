"""
AssetSentinel — Real IBM AI Chat Service
"""

from sqlalchemy.orm import Session
from app.services.watsonx_service import process_message_with_watsonx


def process_chat_message(message: str, db: Session) -> str:
    """
    Process the incoming chat message using IBM Watsonx.ai.
    """

    response = process_message_with_watsonx(message)

    # Prevent empty chatbot messages from reaching the frontend
    if response is None:
        return (
            "I wasn't able to generate a response for that request. "
            "Please try again."
        )

    response = str(response).strip()

    if not response:
        return (
            "I wasn't able to retrieve a response for that request. "
            "Please try again."
        )

    return response