"""FastAPI application entry point for the Conversation AI Agent API."""

import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from fastapi_9.config import get_config

# Configure logging
config = get_config()
logger = logging.getLogger(__name__)
logging.basicConfig(level=config.log_level)


# Global session store and agent manager (will be initialized at startup)
session_store = None
agent_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    # ===== STARTUP =====
    logger.info("=" * 60)
    logger.info("Starting up Conversation AI Agent API")
    logger.info("=" * 60)
    
    global session_store, agent_manager
    
    try:
        from fastapi_9.session_store import SessionStore
        from fastapi_9.agent import AgentManager
        
        # Initialize session store
        logger.info(
            f"Initializing session store: "
            f"ttl_seconds={config.session_ttl_seconds}, "
            f"max_turns={config.session_max_turns}"
        )
        session_store = SessionStore(config.session_ttl_seconds, config.session_max_turns)
        
        # Initialize agent manager
        logger.info(
            f"Initializing agent manager: "
            f"model={config.openai_default_model}, "
            f"temperature={config.openai_default_temperature}"
        )
        agent_manager = AgentManager(config)
        
        logger.info("Session store and agent manager initialized successfully")
        logger.info(f"API available at: http://0.0.0.0:8000")
        logger.info(f"Swagger docs: http://0.0.0.0:8000/docs")
        logger.info(f"ReDoc: http://0.0.0.0:8000/redoc")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}", exc_info=True)
        raise
    
    yield
    
    # ===== SHUTDOWN =====
    logger.info("=" * 60)
    logger.info("Shutting down application")
    logger.info("=" * 60)
    
    try:
        if session_store:
            logger.info("Cleaning up session store...")
            await session_store.cleanup()
            logger.info("Session store cleanup complete")
        
        if agent_manager:
            logger.info("Cleaning up agent manager...")
            # Add any cleanup if needed
            logger.info("Agent manager cleanup complete")
        
        logger.info("Application shutdown complete")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)


# Create FastAPI app instance
app = FastAPI(
    title=config.app_title,
    version=config.app_version,
    description=config.app_description,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "agent",
            "description": "Agent chat endpoints for conversational AI",
        },
        {
            "name": "health",
            "description": "Health check endpoints",
        },
    ],
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CorrelationIDMiddleware:
    """Middleware to add correlation ID to requests and log request/response metadata."""
    
    def __init__(self, app: FastAPI):
        self.app = app
    
    async def __call__(self, request: Request, call_next):
        # Generate or get correlation ID
        correlation_id = request.headers.get("x-correlation-id", str(uuid.uuid4()))
        request.state.correlation_id = correlation_id
        
        # Log request start
        method = request.method
        path = request.url.path
        query_string = request.url.query
        
        logger.debug(
            f"[{correlation_id}] Request started: {method} {path}"
            f"{f'?{query_string}' if query_string else ''}"
        )
        
        # Measure latency
        start_time = time.time()
        
        # Get request body size (for POST/PUT requests)
        request_body = await request.body()
        request_size = len(request_body)
        
        # Get response
        response = await call_next(request)
        
        # Measure response time
        latency_ms = (time.time() - start_time) * 1000
        
        # Get response size
        response_size = len(response.body) if hasattr(response, "body") and response.body else 0
        
        # Add headers
        response.headers["x-correlation-id"] = correlation_id
        response.headers["x-latency-ms"] = str(int(latency_ms))
        
        # Log request/response with structured information
        status_code = response.status_code
        log_level = logging.WARNING if status_code >= 400 else logging.INFO
        
        logger.log(
            log_level,
            f"[{correlation_id}] {method} {path} completed: "
            f"status={status_code} latency_ms={latency_ms:.2f} "
            f"request_size_bytes={request_size} response_size_bytes={response_size}"
        )
        
        return response


app.add_middleware(CorrelationIDMiddleware)


@app.get("/")
async def health_check():
    """
    Health check endpoint.
    
    Returns basic service information.
    """
    return {
        "status": "ok",
        "service": "Conversation AI Agent API",
        "version": config.app_version,
    }


@app.get("/health", tags=["health"])
async def health():
    """
    Detailed health check endpoint.
    
    Returns service health status and current configuration.
    """
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "config": {
            "model": config.openai_default_model,
            "session_ttl_seconds": config.session_ttl_seconds,
            "session_max_turns": config.session_max_turns,
        }
    }


# Import and include chat endpoint after app creation (to avoid circular imports)
from fastapi_9.routes import chat_router  # noqa: E402, F401

app.include_router(chat_router, prefix="/api/agent", tags=["agent"])


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
