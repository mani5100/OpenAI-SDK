"""
FastAPI Chatbot Application with OpenAI Agents SDK

This module serves as the main entry point for the FastAPI-based chatbot API service.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .api.routes import chat, health
from .middleware.error_handler import setup_error_handlers
from .middleware.request_id import RequestIDMiddleware
from .utils.logging import setup_logging

# Configure structured logging
setup_logging(
    log_level=settings.LOG_LEVEL,
    json_logs=settings.LOG_JSON,
)

logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "chat",
            "description": "Chat operations with OpenAI assistant. Create threads, send messages, and manage conversations.",
        },
        {
            "name": "health",
            "description": "Health check endpoints for monitoring API and dependency status.",
        },
    ],
    contact={
        "name": "API Support",
        "url": "https://github.com/mani5100/OpenAI-SDK",
    },
    license_info={
        "name": "MIT",
    },
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request ID tracking middleware
app.add_middleware(RequestIDMiddleware)

# Set up global error handling
setup_error_handlers(app)

# Register API routers
app.include_router(health.router)
app.include_router(chat.router)


@app.get("/")
async def root():
    """Root endpoint providing API information"""
    return {
        "message": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.on_event("startup")
async def startup_event():
    """Execute on application startup"""
    logger.info(
        f"Starting {settings.APP_NAME} v{settings.APP_VERSION}",
        extra={
            "extra_fields": {
                "environment": "Development" if settings.API_RELOAD else "Production",
                "openai_model": settings.OPENAI_CHAT_MODEL,
                "host": settings.API_HOST,
                "port": settings.API_PORT,
            }
        },
    )
    try:
        print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}...")
        print(f"📚 API Documentation available at: /docs")
        print(f"📖 ReDoc Documentation available at: /redoc")
        print(f"🔧 Environment: {'Development' if settings.API_RELOAD else 'Production'}")
        print(f"🤖 OpenAI Model: {settings.OPENAI_CHAT_MODEL}")
    except UnicodeEncodeError:
        # Fallback for Windows console that doesn't support emojis
        print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}...")
        print(f"API Documentation available at: /docs")
        print(f"ReDoc Documentation available at: /redoc")
        print(f"Environment: {'Development' if settings.API_RELOAD else 'Production'}")
        print(f"OpenAI Model: {settings.OPENAI_CHAT_MODEL}")


@app.on_event("shutdown")
async def shutdown_event():
    """Execute on application shutdown"""
    logger.info(f"Shutting down {settings.APP_NAME}")
    try:
        print(f"👋 Shutting down {settings.APP_NAME}...")
    except UnicodeEncodeError:
        print(f"Shutting down {settings.APP_NAME}...")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )
