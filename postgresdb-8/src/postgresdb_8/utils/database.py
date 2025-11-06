"""
Database connection manager for async PostgreSQL operations.

This module provides async database session management using SQLAlchemy
and AsyncPG for optimal PostgreSQL performance.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ..config.settings import Settings


class DatabaseManager:
    """
    Database connection manager for async PostgreSQL operations.
    
    Manages database engine, session factory, and provides context
    managers for database sessions.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize database manager with settings.
        
        Args:
            settings: Application settings instance
        """
        self.settings = settings
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None
    
    @property
    def engine(self) -> AsyncEngine:
        """Get or create async database engine."""
        if self._engine is None:
            self._engine = create_async_engine(
                self.settings.POSTGRES_URL,
                echo=self.settings.LOG_LEVEL == "DEBUG",
                pool_pre_ping=True,  # Verify connections before using
                pool_size=10,  # Connection pool size
                max_overflow=20,  # Additional connections if pool is full
            )
        return self._engine
    
    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get or create async session factory."""
        if self._session_factory is None:
            self._session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,  # Keep objects usable after commit
                autocommit=False,
                autoflush=False,
            )
        return self._session_factory
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get async database session.
        
        Yields:
            AsyncSession: Database session
            
        Example:
            async with db_manager.get_session() as session:
                result = await session.execute(select(User))
        """
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def close(self) -> None:
        """Close database engine and all connections."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
    
    async def health_check(self) -> bool:
        """
        Check database connection health.
        
        Returns:
            bool: True if database is accessible, False otherwise
        """
        try:
            async with self.session_factory() as session:
                await session.execute("SELECT 1")
                return True
        except Exception:
            return False


# Global database manager instance
_db_manager: DatabaseManager | None = None


def get_db_manager(settings: Settings | None = None) -> DatabaseManager:
    """
    Get global database manager instance.
    
    Args:
        settings: Application settings (required on first call)
        
    Returns:
        DatabaseManager: Global database manager instance
        
    Raises:
        ValueError: If settings not provided on first call
    """
    global _db_manager
    
    if _db_manager is None:
        if settings is None:
            raise ValueError("Settings required to initialize database manager")
        _db_manager = DatabaseManager(settings)
    
    return _db_manager


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for getting database sessions.
    
    Yields:
        AsyncSession: Database session
        
    Example:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    db_manager = get_db_manager()
    async for session in db_manager.get_session():
        yield session
