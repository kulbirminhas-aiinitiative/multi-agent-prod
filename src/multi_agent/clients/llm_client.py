"""
HTTP client for LLM Router service
Handles communication with llm-router:8001
"""

import logging
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)


class LLMRouterClient:
    """
    Client for LLM Router service
    Routes chat requests to appropriate LLM providers
    """

    def __init__(self, base_url: str = "http://llm-router:8001"):
        self.base_url = base_url.rstrip("/")
        self.timeout = 60.0  # LLM calls can be slow

    async def chat_completion(
        self,
        persona: str,
        messages: list[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """
        Send chat completion request to LLM Router

        Args:
            persona: Persona name (e.g., "architect", "code_writer")
            messages: List of message dicts with role and content
            system_prompt: Optional system prompt override
            temperature: Sampling temperature
            max_tokens: Max response tokens

        Returns:
            Dict with response content and metadata
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "persona": persona,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }

                if system_prompt:
                    payload["system_prompt"] = system_prompt

                response = await client.post(
                    f"{self.base_url}/api/v1/chat",
                    json=payload
                )
                response.raise_for_status()

                data = response.json()
                logger.info(f"LLM response for persona '{persona}': {len(data.get('content', ''))} chars")
                return data

        except httpx.HTTPError as e:
            logger.error(f"LLM Router request failed: {e}")
            raise Exception(f"LLM Router error: {str(e)}")

    async def health_check(self) -> bool:
        """Check if LLM Router is healthy"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"LLM Router health check failed: {e}")
            return False


# Global client instance
_llm_client = None


def get_llm_client(base_url: str = "http://llm-router:8001") -> LLMRouterClient:
    """Get global LLM client instance"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMRouterClient(base_url=base_url)
    return _llm_client
