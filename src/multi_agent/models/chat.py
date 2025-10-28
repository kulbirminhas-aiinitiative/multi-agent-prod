"""Chat session and message models"""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from enum import Enum


class EngagementMode(str, Enum):
    """Chat engagement modes"""
    SEQUENTIAL = "sequential"  # One after another
    PARALLEL = "parallel"      # All at once
    DEBATE = "debate"          # Discussion/challenges
    CONSENSUS = "consensus"    # Iterate until agreement


class SessionStatus(str, Enum):
    """Chat session status"""
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class MessageRole(str, Enum):
    """Message role"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class RAGConfig(BaseModel):
    """RAG configuration for messages"""
    enable_rag: bool = True
    rag_mode: str = "auto"  # auto, force, disable
    knowledge_types: list[str] = Field(default_factory=lambda: ["sme_docs", "patterns", "history"])
    min_confidence: float = 0.7


class StartChatRequest(BaseModel):
    """Request to start a chat session"""
    engagement_mode: EngagementMode = EngagementMode.SEQUENTIAL
    max_iterations: int = Field(default=5, ge=1, le=20)
    enable_rag: bool = True
    initial_message: Optional[Dict[str, str]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SendMessageRequest(BaseModel):
    """Request to send a message"""
    content: str = Field(..., min_length=1)
    rag_config: Optional[RAGConfig] = None


class RAGInsight(BaseModel):
    """RAG insight from knowledge base"""
    doc_id: str
    content: str
    relevance: float
    source_type: str  # sme_docs, patterns, history


class ChatMessage(BaseModel):
    """Chat message model"""
    id: int
    session_id: UUID
    iteration: int
    turn_order: int
    persona: Optional[str] = None
    role: MessageRole
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)


class ChatMessageResponse(BaseModel):
    """Chat message response with RAG insights"""
    session_id: UUID
    iteration: int
    turn: int
    persona: Optional[str]
    role: MessageRole
    content: str
    rag_insights: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ChatSession(BaseModel):
    """Chat session model"""
    session_id: UUID = Field(default_factory=uuid4)
    team_id: UUID
    engagement_mode: EngagementMode
    max_iterations: int
    current_iteration: int = 0
    status: SessionStatus = SessionStatus.ACTIVE
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None


class ChatSessionResponse(BaseModel):
    """Chat session response"""
    session_id: UUID
    team_id: UUID
    engagement_mode: EngagementMode
    status: SessionStatus
    current_iteration: int
    max_iterations: int
    created_at: datetime


class ConversationHistoryResponse(BaseModel):
    """Conversation history response"""
    session_id: UUID
    iteration: Optional[int] = None
    messages: list[ChatMessageResponse]
    total_messages: int
