"""
Multi-Agent Service - Main FastAPI Application
Orchestrates teams of AI agents with different engagement modes
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .api.v2 import teams_router, chat_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    settings = get_settings()
    logger.info(f"Starting {settings.SERVICE_NAME} v{settings.SERVICE_VERSION}")
    logger.info(f"LLM Router: {settings.LLM_ROUTER_URL}")
    logger.info(f"RAG Service: {settings.RAG_SERVICE_URL}")

    yield

    logger.info(f"Shutting down {settings.SERVICE_NAME}")


# Create FastAPI app
app = FastAPI(
    title="Multi-Agent Service",
    description="Orchestrates teams of AI agents with different engagement modes",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(teams_router)
app.include_router(chat_router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    settings = get_settings()
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "multi-agent-service",
        "version": "1.0.0",
        "description": "Multi-agent orchestration service",
        "endpoints": {
            "health": "/health",
            "teams": "/api/v2/teams",
            "chat": "/api/v2/chat",
        }
    }


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "multi_agent.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
    )
