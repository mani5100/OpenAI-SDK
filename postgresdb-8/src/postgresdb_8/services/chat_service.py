"""Chat service that integrates OpenAI and Database operations."""
from typing import Optional, AsyncGenerator, Dict, Any, Tuple
import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.thread import ConversationThread
from ..models.message import Message, MessageRole
from .openai_service import OpenAIService
from .database_service import DatabaseService

logger = logging.getLogger(__name__)


class ChatService:
    """Integrated service for chat operations combining OpenAI and Database."""
    
    def __init__(
        self,
        openai_service: OpenAIService,
        db_session: AsyncSession
    ):
        """Initialize chat service.
        
        Args:
            openai_service: OpenAI service instance
            db_session: Database session for persistence
        """
        self.openai = openai_service
        self.db = DatabaseService(db_session)
        self.session = db_session
    
    async def create_thread(self) -> ConversationThread:
        """Create a new conversation thread.
        
        Creates thread in both OpenAI and PostgreSQL database.
        
        Returns:
            ConversationThread model instance
            
        Raises:
            Exception: If thread creation fails
        """
        try:
            # Create OpenAI thread
            openai_thread = await self.openai.create_thread()
            logger.info(f"Created OpenAI thread: {openai_thread.id}")
            
            # Store metadata in PostgreSQL
            db_thread = await self.db.create_thread(
                openai_thread_id=openai_thread.id,
                message_count=0,
                total_tokens=0
            )
            await self.session.commit()
            
            logger.info(
                f"Stored thread metadata in DB: {db_thread.id} -> {openai_thread.id}"
            )
            return db_thread
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create thread: {e}")
            raise
    
    async def get_thread(self, thread_id: str) -> Optional[ConversationThread]:
        """Get a conversation thread by database ID.
        
        Args:
            thread_id: Database thread UUID
            
        Returns:
            ConversationThread if found, None otherwise
        """
        return await self.db.get_thread_by_id(thread_id)
    
    async def get_thread_by_openai_id(
        self, openai_thread_id: str
    ) -> Optional[ConversationThread]:
        """Get a conversation thread by OpenAI thread ID.
        
        Args:
            openai_thread_id: OpenAI thread identifier
            
        Returns:
            ConversationThread if found, None otherwise
        """
        return await self.db.get_thread_by_openai_id(openai_thread_id)
    
    async def get_thread_messages(self, thread_id: str) -> list:
        """Get all messages for a thread.
        
        Args:
            thread_id: Thread database ID
            
        Returns:
            List of Message objects
        """
        return await self.db.get_messages_by_thread(thread_id)
    
    async def send_message_non_streaming(
        self,
        thread_id: str,
        user_message: str
    ) -> Dict[str, Any]:
        """Send a message and get non-streaming response.
        
        Complete workflow:
        1. Get thread from database
        2. Send user message to OpenAI
        3. Store user message in database
        4. Get assistant response from OpenAI
        5. Store assistant response in database
        6. Update thread statistics
        
        Args:
            thread_id: Database thread UUID
            user_message: User's message content
            
        Returns:
            Dictionary with response content, message IDs, and usage
            
        Raises:
            ValueError: If thread not found
            Exception: If message sending fails
        """
        try:
            # Get thread from database
            thread = await self.db.get_thread_by_id(thread_id)
            if not thread:
                raise ValueError(f"Thread not found: {thread_id}")
            
            # Get OpenAI response
            response = await self.openai.get_response_non_streaming(
                thread_id=thread.openai_thread_id,
                user_message=user_message
            )
            
            # Store user message in database
            user_msg = await self.db.create_message(
                thread_id=thread_id,
                role=MessageRole.USER,
                content=user_message,
                prompt_tokens=response['usage']['prompt_tokens'],
                completion_tokens=0
            )
            
            # Store assistant response in database
            assistant_msg = await self.db.create_message(
                thread_id=thread_id,
                role=MessageRole.ASSISTANT,
                content=response['content'],
                prompt_tokens=0,
                completion_tokens=response['usage']['completion_tokens']
            )
            
            await self.session.commit()
            
            logger.info(
                f"Stored messages for thread {thread_id}: "
                f"user={user_msg.id}, assistant={assistant_msg.id}"
            )
            
            return {
                "content": response['content'],
                "user_message_id": str(user_msg.id),
                "assistant_message_id": str(assistant_msg.id),
                "openai_run_id": response['run_id'],
                "usage": response['usage'],
                "thread": {
                    "id": str(thread.id),
                    "openai_thread_id": thread.openai_thread_id,
                    "message_count": thread.message_count,
                    "total_tokens": thread.total_tokens
                }
            }
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to send message: {e}")
            raise
    
    async def send_message_streaming(
        self,
        thread_id: str,
        user_message: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Send a message and get streaming response.
        
        Workflow:
        1. Get thread from database
        2. Send user message to OpenAI
        3. Store user message in database
        4. Stream assistant response
        5. Collect full response and store in database
        6. Update thread statistics
        
        Args:
            thread_id: Database thread UUID
            user_message: User's message content
            
        Yields:
            Dictionary with streaming events and data
            
        Raises:
            ValueError: If thread not found
            Exception: If message sending fails
        """
        try:
            # Get thread from database
            thread = await self.db.get_thread_by_id(thread_id)
            if not thread:
                raise ValueError(f"Thread not found: {thread_id}")
            
            # Send user message to OpenAI (but don't run yet)
            await self.openai.send_message(
                thread_id=thread.openai_thread_id,
                content=user_message,
                role="user"
            )
            
            # Collect response data for database storage
            full_response = ""
            token_usage = None
            run_id = None
            
            # Stream the response
            async for event in self.openai.run_assistant_streaming(
                thread_id=thread.openai_thread_id
            ):
                # Yield events to client
                yield event
                
                # Collect data for database
                if event["type"] == "text_delta":
                    full_response += event["delta"]
                elif event["type"] == "run_completed":
                    token_usage = event["usage"]
                elif event["type"] == "run_created":
                    run_id = event["run_id"]
                elif event["type"] == "error":
                    # Don't store if there was an error
                    await self.session.rollback()
                    return
            
            # Store messages in database after streaming completes
            if full_response and token_usage:
                # Store user message
                user_msg = await self.db.create_message(
                    thread_id=thread_id,
                    role=MessageRole.USER,
                    content=user_message,
                    prompt_tokens=token_usage['prompt_tokens'],
                    completion_tokens=0
                )
                
                # Store assistant response
                assistant_msg = await self.db.create_message(
                    thread_id=thread_id,
                    role=MessageRole.ASSISTANT,
                    content=full_response,
                    prompt_tokens=0,
                    completion_tokens=token_usage['completion_tokens']
                )
                
                await self.session.commit()
                
                logger.info(
                    f"Stored streamed messages for thread {thread_id}: "
                    f"user={user_msg.id}, assistant={assistant_msg.id}"
                )
                
                # Yield final event with database IDs
                yield {
                    "type": "storage_complete",
                    "user_message_id": str(user_msg.id),
                    "assistant_message_id": str(assistant_msg.id),
                    "thread": {
                        "id": str(thread.id),
                        "message_count": thread.message_count,
                        "total_tokens": thread.total_tokens
                    }
                }
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to send streaming message: {e}")
            yield {
                "type": "error",
                "error": "service_error",
                "message": str(e)
            }
    
    async def get_thread_history(
        self,
        thread_id: str,
        include_openai: bool = False
    ) -> Dict[str, Any]:
        """Get conversation history for a thread.
        
        Args:
            thread_id: Database thread UUID
            include_openai: If True, also fetch from OpenAI (default: False)
            
        Returns:
            Dictionary with thread info and messages
            
        Raises:
            ValueError: If thread not found
        """
        try:
            thread = await self.db.get_thread_with_messages(thread_id)
            if not thread:
                raise ValueError(f"Thread not found: {thread_id}")
            
            # Get messages from database
            db_messages = await self.db.list_messages_by_thread(thread_id)
            
            result = {
                "thread_id": str(thread.id),
                "openai_thread_id": thread.openai_thread_id,
                "message_count": thread.message_count,
                "total_tokens": thread.total_tokens,
                "created_at": thread.created_at.isoformat(),
                "last_activity_at": thread.last_activity_at.isoformat(),
                "messages": [
                    {
                        "id": str(msg.id),
                        "role": msg.role.value,
                        "content": msg.content,
                        "prompt_tokens": msg.prompt_tokens,
                        "completion_tokens": msg.completion_tokens,
                        "total_tokens": msg.total_tokens,
                        "created_at": msg.created_at.isoformat()
                    }
                    for msg in db_messages
                ]
            }
            
            # Optionally include OpenAI messages for verification
            if include_openai:
                openai_messages = await self.openai.get_thread_messages(
                    thread.openai_thread_id
                )
                result["openai_messages_count"] = len(openai_messages)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get thread history: {e}")
            raise
    
    async def list_threads(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> list[Dict[str, Any]]:
        """List all conversation threads.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of thread dictionaries
        """
        threads = await self.db.list_threads(skip=skip, limit=limit)
        return [
            {
                "id": str(t.id),
                "openai_thread_id": t.openai_thread_id,
                "message_count": t.message_count,
                "total_tokens": t.total_tokens,
                "created_at": t.created_at.isoformat(),
                "last_activity_at": t.last_activity_at.isoformat()
            }
            for t in threads
        ]
    
    async def delete_thread(self, thread_id: str) -> bool:
        """Delete a conversation thread.
        
        Deletes from both database and OpenAI.
        
        Args:
            thread_id: Database thread UUID
            
        Returns:
            True if deletion successful
            
        Raises:
            ValueError: If thread not found
        """
        try:
            thread = await self.db.get_thread_by_id(thread_id)
            if not thread:
                raise ValueError(f"Thread not found: {thread_id}")
            
            # Delete from OpenAI
            try:
                await self.openai.delete_thread(thread.openai_thread_id)
            except Exception as e:
                logger.warning(f"Failed to delete OpenAI thread: {e}")
                # Continue with database deletion even if OpenAI fails
            
            # Delete from database (will cascade to messages)
            deleted = await self.db.delete_thread(thread_id)
            await self.session.commit()
            
            logger.info(f"Deleted thread {thread_id} from both OpenAI and database")
            return deleted
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to delete thread: {e}")
            raise
    
    async def get_thread_statistics(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed statistics for a thread.
        
        Args:
            thread_id: Database thread UUID
            
        Returns:
            Dictionary with thread statistics
        """
        return await self.db.get_thread_statistics(thread_id)
