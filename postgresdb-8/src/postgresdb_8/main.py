"""
FastAPI Chatbot Application with OpenAI Agents SDK

This module serves as the main entry point for the FastAPI-based chatbot API service.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings

# Initialize FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}...")
    print(f"📚 API Documentation available at: /docs")
    print(f"📖 ReDoc Documentation available at: /redoc")
    print(f"🔧 Environment: {'Development' if settings.API_RELOAD else 'Production'}")
    print(f"🤖 OpenAI Model: {settings.OPENAI_CHAT_MODEL}")


@app.on_event("shutdown")
async def shutdown_event():
    """Execute on application shutdown"""
    print(f"👋 Shutting down {settings.APP_NAME}...")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )
