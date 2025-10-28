"""
HTTP client for RAG Service
Handles communication with rag-service:8002
"""

import logging
from typing import Dict, Any, Optional, List
import httpx

logger = logging.getLogger(__name__)


class RAGServiceClient:
    """
    Client for RAG Service
    Handles knowledge queries and context retrieval
    """

    def __init__(self, base_url: str = "http://rag-service:8002"):
        self.base_url = base_url.rstrip("/")
        self.timeout = 10.0

    async def query_knowledge(
        self,
        persona: str,
        query: str,
        knowledge_types: Optional[List[str]] = None,
        top_k: int = 5,
        min_confidence: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Query persona's knowledge base

        Args:
            persona: Persona name
            query: Search query
            knowledge_types: Types of knowledge to search (sme_docs, patterns, history)
            top_k: Number of results to return
            min_confidence: Minimum confidence threshold

        Returns:
            Dict with results and metadata
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "query": query,
                    "collections": knowledge_types or ["sme_docs", "patterns", "history"],
                    "top_k": top_k,
                    "min_confidence": min_confidence,
                }

                response = await client.post(
                    f"{self.base_url}/api/v1/personas/{persona}/query",
                    json=payload
                )
                response.raise_for_status()

                data = response.json()
                logger.info(f"RAG query for persona '{persona}': {len(data.get('results', []))} results")
                return data

        except httpx.HTTPError as e:
            logger.error(f"RAG Service request failed: {e}")
            # Return empty results instead of failing
            return {
                "results": [],
                "total": 0,
                "query": query,
                "error": str(e)
            }

    async def get_context(
        self,
        persona: str,
        session_id: str,
        iteration: int,
    ) -> Dict[str, Any]:
        """
        Get conversation context from RAG service

        Args:
            persona: Persona name
            session_id: Session identifier
            iteration: Current iteration number

        Returns:
            Dict with conversation context
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/context/{persona}/{session_id}",
                    params={"iteration": iteration}
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPError as e:
            logger.error(f"RAG context retrieval failed: {e}")
            return {
                "conversation_history": [],
                "team_context": {},
            }

    async def store_interaction(
        self,
        persona: str,
        session_id: str,
        team_id: str,
        iteration: int,
        turn: int,
        message: str,
        response: str,
        rag_insights: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Store interaction in RAG service for future context

        Returns:
            True if successful
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "persona": persona,
                    "session_id": session_id,
                    "team_id": team_id,
                    "iteration": iteration,
                    "turn": turn,
                    "message": message,
                    "response": response,
                    "rag_insights": rag_insights,
                }

                response = await client.post(
                    f"{self.base_url}/api/v1/interactions/store",
                    json=payload
                )
                response.raise_for_status()
                return True

        except httpx.HTTPError as e:
            logger.error(f"Store interaction failed: {e}")
            return False

    async def health_check(self) -> bool:
        """Check if RAG Service is healthy"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"RAG Service health check failed: {e}")
            return False


# Global client instance
_rag_client = None


def get_rag_client(base_url: str = "http://rag-service:8002") -> RAGServiceClient:
    """Get global RAG client instance"""
    global _rag_client
    if _rag_client is None:
        _rag_client = RAGServiceClient(base_url=base_url)
    return _rag_client
