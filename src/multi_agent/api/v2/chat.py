"""
V2 API - Chat Sessions
RAG-enhanced multi-agent conversations
"""

import logging
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends

from ...models import (
    StartChatRequest,
    SendMessageRequest,
    ChatSessionResponse,
    ChatMessageResponse,
    ConversationHistoryResponse,
)
from ...services import ChatService, get_chat_service
from ...config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/chat", tags=["v2-chat"])


def get_chat_service_instance() -> ChatService:
    """Dependency to get chat service"""
    settings = get_settings()
    return get_chat_service(
        llm_url=settings.LLM_ROUTER_URL,
        rag_url=settings.RAG_SERVICE_URL
    )


@router.post("/teams/{team_id}/sessions", response_model=ChatSessionResponse)
async def create_session(
    team_id: UUID,
    request: StartChatRequest,
    chat_service: ChatService = Depends(get_chat_service_instance)
):
    """
    Start a new chat session with a team

    Engagement modes:
    - sequential: Personas respond one after another
    - parallel: All personas respond simultaneously
    - debate: Personas challenge each other
    - consensus: Iterate until agreement

    Example:
    ```json
    {
      "engagement_mode": "sequential",
      "max_iterations": 5,
      "enable_rag": true,
      "initial_message": {
        "content": "Design authentication for microservices"
      }
    }
    ```
    """
    try:
        session = await chat_service.create_session(team_id, request)
        return session
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Session creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/message", response_model=ChatMessageResponse)
async def send_message(
    session_id: UUID,
    request: SendMessageRequest,
    chat_service: ChatService = Depends(get_chat_service_instance)
):
    """
    Send a message to a chat session

    The team will process the message according to the engagement mode.
    RAG can be enabled per message.

    Example:
    ```json
    {
      "content": "Add OAuth2 support to the design",
      "rag_config": {
        "enable_rag": true,
        "knowledge_types": ["sme_docs", "patterns"],
        "min_confidence": 0.7
      }
    }
    ```
    """
    try:
        response = await chat_service.send_message(session_id, request)
        return response
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Send message failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_session(
    session_id: UUID,
    chat_service: ChatService = Depends(get_chat_service_instance)
):
    """Get session details"""
    session = await chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/sessions/{session_id}/messages", response_model=ConversationHistoryResponse)
async def get_messages(
    session_id: UUID,
    iteration: Optional[int] = None,
    chat_service: ChatService = Depends(get_chat_service_instance)
):
    """
    Get conversation messages

    Optional: Filter by iteration
    """
    try:
        history = await chat_service.get_messages(session_id, iteration)
        return history
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: UUID,
    chat_service: ChatService = Depends(get_chat_service_instance)
):
    """Delete a chat session"""
    success = await chat_service.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "deleted", "session_id": str(session_id)}
