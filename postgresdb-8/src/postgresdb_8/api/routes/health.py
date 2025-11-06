"""Health check endpoint for monitoring API and dependencies."""

import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ...config import settings
from ...services import OpenAIService
from ..dependencies import get_db_session


router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/health")
async def health_check(
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    Health check endpoint that verifies connectivity to all dependencies.
    
    Checks:
    - API service status
    - Database connectivity
    - OpenAI API connectivity
    
    Args:
        db: Database session (injected)
        
    Returns:
        dict: Health status of the API and all dependencies
    """
    logger.info("Health check requested")
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": settings.APP_VERSION,
        "checks": {
            "api": {"status": "healthy"},
            "database": {"status": "unknown"},
            "openai": {"status": "unknown"},
        }
    }
    
    # Check database connectivity
    try:
        logger.debug("Checking database connectivity")
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
        logger.debug("Database check: healthy")
        
    except Exception as e:
        logger.error(
            f"Database health check failed: {str(e)}",
            extra={"extra_fields": {"error_type": type(e).__name__}},
            exc_info=True,
        )
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}",
            "error": type(e).__name__,
        }
        health_status["status"] = "unhealthy"
    
    # Check OpenAI API connectivity
    try:
        logger.debug("Checking OpenAI API connectivity")
        openai_service = OpenAIService()
        
        # Try to list models as a lightweight connectivity check
        # This verifies API key is valid and service is reachable
        models = await openai_service.client.models.list()
        
        health_status["checks"]["openai"] = {
            "status": "healthy",
            "message": "OpenAI API connection successful",
            "model": settings.OPENAI_CHAT_MODEL,
        }
        logger.debug("OpenAI API check: healthy")
        
    except Exception as e:
        logger.error(
            f"OpenAI API health check failed: {str(e)}",
            extra={"extra_fields": {"error_type": type(e).__name__}},
            exc_info=True,
        )
        health_status["checks"]["openai"] = {
            "status": "unhealthy",
            "message": f"OpenAI API connection failed: {str(e)}",
            "error": type(e).__name__,
        }
        health_status["status"] = "unhealthy"
    
    # Log overall health status
    if health_status["status"] == "healthy":
        logger.info("Health check: All systems healthy")
    else:
        logger.warning(
            "Health check: System unhealthy",
            extra={"extra_fields": {"checks": health_status["checks"]}}
        )
    
    return health_status


@router.get("/health/live")
async def liveness_check() -> Dict[str, str]:
    """
    Liveness probe endpoint for Kubernetes/container orchestration.
    
    Returns a simple response indicating the API is running.
    Does not check dependencies.
    
    Returns:
        dict: Simple status message
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/health/ready")
async def readiness_check(
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    Readiness probe endpoint for Kubernetes/container orchestration.
    
    Checks if the API is ready to handle requests by verifying
    critical dependencies (database).
    
    Args:
        db: Database session (injected)
        
    Returns:
        dict: Readiness status
        
    Raises:
        HTTPException: 503 if not ready
    """
    logger.debug("Readiness check requested")
    
    ready = True
    checks = {}
    
    # Check database connectivity (critical for readiness)
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        checks["database"] = "ready"
    except Exception as e:
        logger.error(
            f"Readiness check failed: {str(e)}",
            extra={"extra_fields": {"error_type": type(e).__name__}},
        )
        checks["database"] = "not ready"
        ready = False
    
    response = {
        "status": "ready" if ready else "not ready",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "checks": checks,
    }
    
    # Return 503 if not ready (Kubernetes will not route traffic)
    if not ready:
        from fastapi import Response
        return Response(
            content=str(response),
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            media_type="application/json",
        )
    
    return response
