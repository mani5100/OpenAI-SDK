"""Database service layer for CRUD operations on threads and messages."""
from typing import Optional, Sequence
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.thread import ConversationThread
from ..models.message import Message, MessageRole


class DatabaseService:
    """Service layer for database operations on conversation threads and messages."""
    
    def __init__(self, session: AsyncSession):
        """Initialize database service with a session.
        
        Args:
            session: Async SQLAlchemy session
        """
        self.session = session
    
    # ==================== ConversationThread CRUD ====================
    
    async def create_thread(
        self,
        openai_thread_id: str,
        message_count: int = 0,
        total_tokens: int = 0,
    ) -> ConversationThread:
        """Create a new conversation thread.
        
        Args:
            openai_thread_id: OpenAI thread identifier
            message_count: Initial message count (default: 0)
            total_tokens: Initial token count (default: 0)
            
        Returns:
            Created ConversationThread instance
        """
        thread = ConversationThread(
            id=str(uuid4()),
            openai_thread_id=openai_thread_id,
            last_activity_at=datetime.now(timezone.utc),
            message_count=message_count,
            total_tokens=total_tokens,
        )
        self.session.add(thread)
        await self.session.flush()
        await self.session.refresh(thread)
        return thread
    
    async def get_thread_by_id(self, thread_id: str) -> Optional[ConversationThread]:
        """Get a conversation thread by ID.
        
        Args:
            thread_id: Thread UUID
            
        Returns:
            ConversationThread if found, None otherwise
        """
        try:
            result = await self.session.execute(
                select(ConversationThread).where(ConversationThread.id == thread_id)
            )
            return result.scalar_one_or_none()
        except Exception:
            # Invalid UUID format or other database error
            return None
    
    async def get_thread_by_openai_id(
        self, openai_thread_id: str
    ) -> Optional[ConversationThread]:
        """Get a conversation thread by OpenAI thread ID.
        
        Args:
            openai_thread_id: OpenAI thread identifier
            
        Returns:
            ConversationThread if found, None otherwise
        """
        result = await self.session.execute(
            select(ConversationThread).where(
                ConversationThread.openai_thread_id == openai_thread_id
            )
        )
        return result.scalar_one_or_none()
    
    async def get_thread_with_messages(
        self, thread_id: str
    ) -> Optional[ConversationThread]:
        """Get a conversation thread with all its messages eagerly loaded.
        
        Args:
            thread_id: Thread UUID
            
        Returns:
            ConversationThread with messages if found, None otherwise
        """
        result = await self.session.execute(
            select(ConversationThread)
            .options(selectinload(ConversationThread.messages))
            .where(ConversationThread.id == thread_id)
        )
        return result.scalar_one_or_none()
    
    async def list_threads(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by_activity: bool = True,
    ) -> Sequence[ConversationThread]:
        """List conversation threads with pagination.
        
        Args:
            skip: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)
            order_by_activity: If True, order by last_activity_at descending (default: True)
            
        Returns:
            List of ConversationThread instances
        """
        query = select(ConversationThread)
        
        if order_by_activity:
            query = query.order_by(desc(ConversationThread.last_activity_at))
        else:
            query = query.order_by(desc(ConversationThread.created_at))
        
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update_thread_activity(
        self, thread_id: str
    ) -> Optional[ConversationThread]:
        """Update thread's last activity timestamp.
        
        Args:
            thread_id: Thread UUID
            
        Returns:
            Updated ConversationThread if found, None otherwise
        """
        thread = await self.get_thread_by_id(thread_id)
        if thread:
            thread.update_activity()
            await self.session.flush()
            await self.session.refresh(thread)
        return thread
    
    async def delete_thread(self, thread_id: str) -> bool:
        """Delete a conversation thread (will cascade delete all messages).
        
        Args:
            thread_id: Thread UUID
            
        Returns:
            True if thread was deleted, False if not found
        """
        thread = await self.get_thread_by_id(thread_id)
        if thread:
            await self.session.delete(thread)
            await self.session.flush()
            return True
        return False
    
    # ==================== Message CRUD ====================
    
    async def create_message(
        self,
        thread_id: str,
        role: MessageRole,
        content: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
    ) -> Optional[Message]:
        """Create a new message in a conversation thread.
        
        Args:
            thread_id: Thread UUID
            role: Message role (USER or ASSISTANT)
            content: Message content text
            prompt_tokens: Number of tokens in the prompt (default: 0)
            completion_tokens: Number of tokens in the completion (default: 0)
            
        Returns:
            Created Message instance if thread exists, None otherwise
        """
        # Verify thread exists
        thread = await self.get_thread_by_id(thread_id)
        if not thread:
            return None
        
        message = Message(
            id=str(uuid4()),
            thread_id=thread_id,
            role=role,
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
        self.session.add(message)
        
        # Update thread statistics
        thread.message_count += 1
        thread.total_tokens += message.total_tokens
        thread.update_activity()
        
        await self.session.flush()
        await self.session.refresh(message)
        return message
    
    async def get_message_by_id(self, message_id: str) -> Optional[Message]:
        """Get a message by ID.
        
        Args:
            message_id: Message UUID
            
        Returns:
            Message if found, None otherwise
        """
        result = await self.session.execute(
            select(Message).where(Message.id == message_id)
        )
        return result.scalar_one_or_none()
    
    async def list_messages_by_thread(
        self,
        thread_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Message]:
        """List all messages in a conversation thread.
        
        Args:
            thread_id: Thread UUID
            skip: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)
            
        Returns:
            List of Message instances ordered by creation time
        """
        result = await self.session.execute(
            select(Message)
            .where(Message.thread_id == thread_id)
            .order_by(Message.created_at)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_latest_message(self, thread_id: str) -> Optional[Message]:
        """Get the most recent message in a thread.
        
        Args:
            thread_id: Thread UUID
            
        Returns:
            Latest Message if exists, None otherwise
        """
        result = await self.session.execute(
            select(Message)
            .where(Message.thread_id == thread_id)
            .order_by(desc(Message.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def count_messages_by_thread(self, thread_id: str) -> int:
        """Count total messages in a thread.
        
        Args:
            thread_id: Thread UUID
            
        Returns:
            Number of messages in the thread
        """
        result = await self.session.execute(
            select(func.count()).select_from(Message).where(Message.thread_id == thread_id)
        )
        return result.scalar() or 0
    
    async def delete_message(self, message_id: str) -> bool:
        """Delete a message and update thread statistics.
        
        Args:
            message_id: Message UUID
            
        Returns:
            True if message was deleted, False if not found
        """
        message = await self.get_message_by_id(message_id)
        if not message:
            return False
        
        # Get thread to update statistics
        thread = await self.get_thread_by_id(message.thread_id)
        if thread:
            thread.message_count = max(0, thread.message_count - 1)
            thread.total_tokens = max(0, thread.total_tokens - message.total_tokens)
            thread.update_activity()
        
        await self.session.delete(message)
        await self.session.flush()
        return True
    
    # ==================== Utility Methods ====================
    
    async def get_thread_statistics(self, thread_id: str) -> Optional[dict]:
        """Get statistics for a conversation thread.
        
        Args:
            thread_id: Thread UUID
            
        Returns:
            Dictionary with thread statistics or None if thread not found
        """
        thread = await self.get_thread_by_id(thread_id)
        if not thread:
            return None
        
        message_count = await self.count_messages_by_thread(thread_id)
        
        # Get token statistics
        result = await self.session.execute(
            select(
                func.sum(Message.prompt_tokens).label('total_prompt_tokens'),
                func.sum(Message.completion_tokens).label('total_completion_tokens'),
                func.avg(Message.prompt_tokens).label('avg_prompt_tokens'),
                func.avg(Message.completion_tokens).label('avg_completion_tokens'),
            ).where(Message.thread_id == thread_id)
        )
        stats = result.one()
        
        return {
            'thread_id': thread_id,
            'openai_thread_id': thread.openai_thread_id,
            'message_count': message_count,
            'total_prompt_tokens': int(stats.total_prompt_tokens or 0),
            'total_completion_tokens': int(stats.total_completion_tokens or 0),
            'total_tokens': thread.total_tokens,
            'avg_prompt_tokens': float(stats.avg_prompt_tokens or 0),
            'avg_completion_tokens': float(stats.avg_completion_tokens or 0),
            'created_at': thread.created_at,
            'last_activity_at': thread.last_activity_at,
        }
    
    async def search_messages(
        self,
        search_term: str,
        thread_id: Optional[str] = None,
        limit: int = 50,
    ) -> Sequence[Message]:
        """Search messages by content.
        
        Args:
            search_term: Text to search for in message content
            thread_id: Optional thread ID to limit search to specific thread
            limit: Maximum number of results (default: 50)
            
        Returns:
            List of matching Message instances
        """
        query = select(Message).where(Message.content.ilike(f'%{search_term}%'))
        
        if thread_id:
            query = query.where(Message.thread_id == thread_id)
        
        query = query.order_by(desc(Message.created_at)).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()
