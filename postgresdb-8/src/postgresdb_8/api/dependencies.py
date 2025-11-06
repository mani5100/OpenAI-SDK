"""FastAPI dependency injection for database and services."""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from ..utils.database import get_db_manager
from ..services import ChatService
from ..config import settings


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    
    Yields:
        AsyncSession: Database session for the request.
        
    Example:
        ```python
        @app.get("/example")
        async def example(db: AsyncSession = Depends(get_db_session)):
            # Use db session here
            pass
        ```
    """
    db_manager = get_db_manager(settings)
    async for session in db_manager.get_session():
        yield session


async def get_chat_service(
    db: AsyncSession = None
) -> ChatService:
    """
    Dependency to get ChatService instance.
    
    Args:
        db: Database session (optional, will create if not provided)
        
    Returns:
        ChatService: Initialized ChatService instance
        
    Example:
        ```python
        @app.post("/chat/message")
        async def chat(
            chat_service: ChatService = Depends(get_chat_service),
            db: AsyncSession = Depends(get_db_session)
        ):
            # Use chat_service here
            pass
        ```
    """
    if db is None:
        db_manager = get_db_manager(settings)
        async for session in db_manager.get_session():
            return ChatService(session)
    return ChatService(db)
