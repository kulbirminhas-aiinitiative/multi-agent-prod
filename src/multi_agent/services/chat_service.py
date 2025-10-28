"""
Chat Service
Business logic for chat sessions with RAG-enhanced multi-agent conversations
Uses HTTP clients to call external LLM and RAG services
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from ..models import (
    ChatSession,
    ChatSessionResponse,
    ChatMessage,
    ChatMessageResponse,
    ConversationHistoryResponse,
    StartChatRequest,
    SendMessageRequest,
    EngagementMode,
    SessionStatus,
    MessageRole,
)
from ..clients import get_llm_client, get_rag_client
from .team_service import get_team_service

logger = logging.getLogger(__name__)


class ChatService:
    """
    Service for managing chat sessions and RAG-enhanced conversations

    Handles:
    - Session creation and management
    - Multi-agent engagement modes (sequential, parallel, debate, consensus)
    - RAG integration per persona via HTTP
    - LLM calls via HTTP to llm-router
    """

    def __init__(self, llm_url: str = "http://llm-router:8001", rag_url: str = "http://rag-service:8002"):
        # In-memory storage for MVP
        self.sessions: dict[UUID, ChatSession] = {}
        self.messages: dict[UUID, List[ChatMessage]] = {}
        self._message_id_counter = 1

        # HTTP clients
        self.llm_client = get_llm_client(base_url=llm_url)
        self.rag_client = get_rag_client(base_url=rag_url)

        # Team service
        self.team_service = get_team_service()

        logger.info("ChatService initialized with HTTP clients")

    async def create_session(
        self,
        team_id: UUID,
        request: StartChatRequest
    ) -> ChatSessionResponse:
        """Create a new chat session"""

        # Verify team exists
        team = await self.team_service.get_team(team_id)
        if not team:
            raise ValueError(f"Team not found: {team_id}")

        # Create session
        session = ChatSession(
            team_id=team_id,
            engagement_mode=request.engagement_mode,
            max_iterations=request.max_iterations,
            metadata=request.metadata,
            expires_at=datetime.now() + timedelta(hours=24),
        )

        self.sessions[session.session_id] = session
        self.messages[session.session_id] = []

        logger.info(
            f"Created session: {session.session_id} "
            f"(team: {team.name}, mode: {request.engagement_mode.value})"
        )

        # If initial message provided, process it
        if request.initial_message:
            await self.send_message(
                session.session_id,
                SendMessageRequest(
                    content=request.initial_message.get("content", ""),
                    rag_config=None if not request.enable_rag else {}
                )
            )

        return ChatSessionResponse(
            session_id=session.session_id,
            team_id=session.team_id,
            engagement_mode=session.engagement_mode,
            status=session.status,
            current_iteration=session.current_iteration,
            max_iterations=session.max_iterations,
            created_at=session.created_at,
        )

    async def send_message(
        self,
        session_id: UUID,
        request: SendMessageRequest
    ) -> ChatMessageResponse:
        """
        Send a message and get response from team

        Handles engagement modes:
        - Sequential: One persona at a time
        - Parallel: All personas respond simultaneously
        - Debate: Personas challenge each other
        - Consensus: Iterate until agreement
        """

        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        if session.status != SessionStatus.ACTIVE:
            raise ValueError(f"Session is not active: {session.status}")

        # Store user message
        user_msg = ChatMessage(
            id=self._message_id_counter,
            session_id=session_id,
            iteration=session.current_iteration + 1,
            turn_order=0,
            persona=None,
            role=MessageRole.USER,
            content=request.content,
            metadata={"rag_config": request.rag_config.dict() if request.rag_config else {}},
        )
        self._message_id_counter += 1
        self.messages[session_id].append(user_msg)

        # Increment iteration
        session.current_iteration += 1
        session.updated_at = datetime.now()

        # Get team members
        team_members = await self.team_service.get_members(session.team_id)

        # Process based on engagement mode
        if session.engagement_mode == EngagementMode.SEQUENTIAL:
            response = await self._process_sequential(
                session, team_members, request.content, request.rag_config
            )
        elif session.engagement_mode == EngagementMode.PARALLEL:
            response = await self._process_parallel(
                session, team_members, request.content, request.rag_config
            )
        elif session.engagement_mode == EngagementMode.DEBATE:
            response = await self._process_debate(
                session, team_members, request.content, request.rag_config
            )
        else:  # CONSENSUS
            response = await self._process_consensus(
                session, team_members, request.content, request.rag_config
            )

        # Check if max iterations reached
        if session.current_iteration >= session.max_iterations:
            session.status = SessionStatus.COMPLETED
            logger.info(f"Session completed: {session_id}")

        return response

    async def _process_sequential(
        self,
        session: ChatSession,
        team_members: List,
        message: str,
        rag_config: Any
    ) -> ChatMessageResponse:
        """Process message sequentially through team members"""

        # For MVP, just use first persona
        if not team_members:
            raise ValueError("No team members available")

        persona_member = team_members[0]

        # Get RAG context if enabled
        enable_rag = rag_config is not None if rag_config else False
        rag_insights = None

        if enable_rag:
            try:
                rag_result = await self.rag_client.query_knowledge(
                    persona=persona_member.persona,
                    query=message,
                    knowledge_types=rag_config.knowledge_types if rag_config else None,
                    top_k=5,
                    min_confidence=rag_config.min_confidence if rag_config else 0.7,
                )
                rag_insights = rag_result
            except Exception as e:
                logger.warning(f"RAG query failed: {e}")

        # Get conversation context
        try:
            context = await self.rag_client.get_context(
                persona=persona_member.persona,
                session_id=str(session.session_id),
                iteration=session.current_iteration,
            )
        except Exception as e:
            logger.warning(f"Context retrieval failed: {e}")
            context = {}

        # Build prompt with context
        prompt = self._build_prompt_with_context(message, context, rag_insights)

        # Get LLM response via HTTP
        try:
            llm_response = await self.llm_client.chat_completion(
                persona=persona_member.persona,
                messages=[{"role": "user", "content": prompt}],
                system_prompt=persona_member.system_prompt,
                temperature=0.7,
                max_tokens=2048,
            )
            response_content = llm_response.get("content", "")
        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            response_content = f"[Error] Failed to get response from LLM: {str(e)}"

        # Store response
        response_msg = ChatMessage(
            id=self._message_id_counter,
            session_id=session.session_id,
            iteration=session.current_iteration,
            turn_order=1,
            persona=persona_member.persona,
            role=MessageRole.ASSISTANT,
            content=response_content,
            metadata={"rag_used": enable_rag},
        )
        self._message_id_counter += 1
        self.messages[session.session_id].append(response_msg)

        # Store interaction in RAG service
        try:
            await self.rag_client.store_interaction(
                persona=persona_member.persona,
                session_id=str(session.session_id),
                team_id=str(session.team_id),
                iteration=session.current_iteration,
                turn=1,
                message=message,
                response=response_content,
                rag_insights=rag_insights,
            )
        except Exception as e:
            logger.warning(f"Store interaction failed: {e}")

        return ChatMessageResponse(
            session_id=session.session_id,
            iteration=session.current_iteration,
            turn=1,
            persona=persona_member.persona,
            role=MessageRole.ASSISTANT,
            content=response_content,
            rag_insights=rag_insights,
            metadata={"engagement_mode": session.engagement_mode.value},
            created_at=response_msg.created_at,
        )

    async def _process_parallel(self, session, team_members, message, rag_config):
        """Process message in parallel (all personas respond simultaneously)"""
        # TODO: Implement parallel processing
        return await self._process_sequential(session, team_members, message, rag_config)

    async def _process_debate(self, session, team_members, message, rag_config):
        """Process message as debate (personas challenge each other)"""
        # TODO: Implement debate mode
        return await self._process_sequential(session, team_members, message, rag_config)

    async def _process_consensus(self, session, team_members, message, rag_config):
        """Process message seeking consensus (iterate until agreement)"""
        # TODO: Implement consensus mode
        return await self._process_sequential(session, team_members, message, rag_config)

    def _build_prompt_with_context(
        self,
        message: str,
        context: Dict[str, Any],
        rag_insights: Optional[Dict[str, Any]]
    ) -> str:
        """Build LLM prompt with RAG context"""

        prompt_parts = []

        # Add conversation history
        if context.get("conversation_history"):
            prompt_parts.append("# Conversation History")
            for hist in context["conversation_history"][-5:]:  # Last 5 turns
                prompt_parts.append(f"- {hist.get('persona', 'User')}: {hist.get('message', '')}...")

        # Add RAG insights
        if rag_insights and rag_insights.get("results"):
            prompt_parts.append("\n# Relevant Knowledge")
            for result in rag_insights["results"][:3]:
                prompt_parts.append(f"- ({result.get('source_type', 'unknown')}) {result.get('content', '')[:100]}...")

        # Add team context
        if context.get("team_context") and context["team_context"].get("messages"):
            prompt_parts.append("\n# Team Discussion")
            for msg in context["team_context"]["messages"]:
                prompt_parts.append(f"- {msg.get('persona')}: {msg.get('response', '')[:100]}...")

        # Add current message
        prompt_parts.append(f"\n# Current Request\n{message}")

        return "\n".join(prompt_parts)

    async def get_session(self, session_id: UUID) -> Optional[ChatSessionResponse]:
        """Get session details"""

        session = self.sessions.get(session_id)
        if not session:
            return None

        return ChatSessionResponse(
            session_id=session.session_id,
            team_id=session.team_id,
            engagement_mode=session.engagement_mode,
            status=session.status,
            current_iteration=session.current_iteration,
            max_iterations=session.max_iterations,
            created_at=session.created_at,
        )

    async def get_messages(
        self,
        session_id: UUID,
        iteration: Optional[int] = None
    ) -> ConversationHistoryResponse:
        """Get conversation messages"""

        if session_id not in self.sessions:
            raise ValueError(f"Session not found: {session_id}")

        all_messages = self.messages.get(session_id, [])

        # Filter by iteration if specified
        if iteration is not None:
            filtered = [m for m in all_messages if m.iteration == iteration]
        else:
            filtered = all_messages

        # Convert to response format
        message_responses = [
            ChatMessageResponse(
                session_id=m.session_id,
                iteration=m.iteration,
                turn=m.turn_order,
                persona=m.persona,
                role=m.role,
                content=m.content,
                rag_insights=m.metadata.get("rag_insights"),
                metadata=m.metadata,
                created_at=m.created_at,
            )
            for m in filtered
        ]

        return ConversationHistoryResponse(
            session_id=session_id,
            iteration=iteration,
            messages=message_responses,
            total_messages=len(message_responses),
        )

    async def delete_session(self, session_id: UUID) -> bool:
        """Delete a session"""

        if session_id not in self.sessions:
            return False

        del self.sessions[session_id]
        del self.messages[session_id]

        logger.info(f"Deleted session: {session_id}")

        return True


# Global service instance
_chat_service = None


def get_chat_service(
    llm_url: str = "http://llm-router:8001",
    rag_url: str = "http://rag-service:8002"
) -> ChatService:
    """Get global chat service instance"""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService(llm_url=llm_url, rag_url=rag_url)
    return _chat_service
