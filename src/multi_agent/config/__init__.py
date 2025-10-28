"""Configuration module"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""

    # Service info
    SERVICE_NAME: str = "multi-agent-service"
    SERVICE_VERSION: str = "1.0.0"
    PORT: int = 8003

    # External services
    LLM_ROUTER_URL: str = "http://llm-router:8001"
    RAG_SERVICE_URL: str = "http://rag-service:8002"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/3"

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
