"""OpenAI service for managing assistants, threads, and message interactions."""
from typing import Optional, AsyncGenerator, Dict, Any
import logging
import asyncio

from openai import AsyncOpenAI, OpenAIError, APIError, RateLimitError, APIConnectionError
from openai.types.beta import Assistant, Thread
from openai.types.beta.threads import Run, Message as OpenAIMessage
from openai.types.beta.threads.runs import RunStep

from ..config.settings import Settings

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for interacting with OpenAI Assistants API."""
    
    def __init__(self, settings: Settings):
        """Initialize OpenAI service with configuration.
        
        Args:
            settings: Application settings with OpenAI configuration
        """
        self.settings = settings
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self._assistant: Optional[Assistant] = None
        
        logger.info(
            f"OpenAI service initialized with model: {settings.OPENAI_CHAT_MODEL}"
        )
    
    async def get_or_create_assistant(self) -> Assistant:
        """Get existing assistant or create a new one.
        
        Creates an assistant with configured name, instructions, and model.
        Caches the assistant instance for reuse.
        
        Returns:
            OpenAI Assistant instance
            
        Raises:
            OpenAIError: If assistant creation/retrieval fails
        """
        if self._assistant:
            return self._assistant
        
        try:
            # Try to find existing assistant by name
            assistants = await self.client.beta.assistants.list()
            for assistant in assistants.data:
                if assistant.name == self.settings.OPENAI_ASSISTANT_NAME:
                    logger.info(f"Found existing assistant: {assistant.id}")
                    self._assistant = assistant
                    return self._assistant
            
            # Create new assistant if not found
            logger.info(
                f"Creating new assistant: {self.settings.OPENAI_ASSISTANT_NAME}"
            )
            self._assistant = await self.client.beta.assistants.create(
                name=self.settings.OPENAI_ASSISTANT_NAME,
                instructions=self.settings.OPENAI_ASSISTANT_INSTRUCTIONS,
                model=self.settings.OPENAI_CHAT_MODEL,
                temperature=self.settings.OPENAI_TEMPERATURE,
            )
            logger.info(f"Created assistant: {self._assistant.id}")
            return self._assistant
            
        except OpenAIError as e:
            logger.error(f"Failed to get/create assistant: {e}")
            raise
    
    async def create_thread(self) -> Thread:
        """Create a new conversation thread.
        
        Returns:
            OpenAI Thread instance
            
        Raises:
            OpenAIError: If thread creation fails
        """
        try:
            thread = await self.client.beta.threads.create()
            logger.info(f"Created thread: {thread.id}")
            return thread
        except OpenAIError as e:
            logger.error(f"Failed to create thread: {e}")
            raise
    
    async def get_thread(self, thread_id: str) -> Thread:
        """Retrieve an existing thread.
        
        Args:
            thread_id: OpenAI thread ID
            
        Returns:
            OpenAI Thread instance
            
        Raises:
            OpenAIError: If thread retrieval fails
        """
        try:
            thread = await self.client.beta.threads.retrieve(thread_id)
            return thread
        except OpenAIError as e:
            logger.error(f"Failed to retrieve thread {thread_id}: {e}")
            raise
    
    async def send_message(
        self,
        thread_id: str,
        content: str,
        role: str = "user"
    ) -> OpenAIMessage:
        """Send a message to a thread.
        
        Args:
            thread_id: OpenAI thread ID
            content: Message content text
            role: Message role (default: "user")
            
        Returns:
            OpenAI Message instance
            
        Raises:
            OpenAIError: If message sending fails
        """
        try:
            message = await self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role=role,
                content=content
            )
            logger.debug(f"Sent message to thread {thread_id}: {message.id}")
            return message
        except OpenAIError as e:
            logger.error(f"Failed to send message to thread {thread_id}: {e}")
            raise
    
    async def run_assistant(
        self,
        thread_id: str,
        assistant_id: Optional[str] = None
    ) -> Run:
        """Run the assistant on a thread to generate a response.
        
        Args:
            thread_id: OpenAI thread ID
            assistant_id: Optional assistant ID (uses default if not provided)
            
        Returns:
            OpenAI Run instance
            
        Raises:
            OpenAIError: If run creation fails
        """
        if not assistant_id:
            assistant = await self.get_or_create_assistant()
            assistant_id = assistant.id
        
        try:
            run = await self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id,
                max_prompt_tokens=self.settings.OPENAI_MAX_TOKENS,
            )
            logger.debug(f"Started run {run.id} on thread {thread_id}")
            return run
        except OpenAIError as e:
            logger.error(f"Failed to run assistant on thread {thread_id}: {e}")
            raise
    
    async def wait_for_run_completion(
        self,
        thread_id: str,
        run_id: str,
        poll_interval: float = 0.5
    ) -> Run:
        """Wait for a run to complete.
        
        Polls the run status until it completes, fails, or requires action.
        
        Args:
            thread_id: OpenAI thread ID
            run_id: Run ID to wait for
            poll_interval: Seconds between status checks (default: 0.5)
            
        Returns:
            Completed Run instance
            
        Raises:
            OpenAIError: If run fails or times out
        """
        import asyncio
        
        try:
            while True:
                run = await self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run_id
                )
                
                if run.status == "completed":
                    logger.debug(f"Run {run_id} completed")
                    return run
                elif run.status in ["failed", "cancelled", "expired"]:
                    logger.error(f"Run {run_id} ended with status: {run.status}")
                    raise OpenAIError(
                        f"Run failed with status: {run.status}. "
                        f"Last error: {run.last_error}"
                    )
                elif run.status == "requires_action":
                    logger.warning(
                        f"Run {run_id} requires action (tool calls not implemented)"
                    )
                    # For now, we don't handle tool calls
                    raise OpenAIError("Run requires action - tool calls not supported")
                
                # Poll again after interval
                await asyncio.sleep(poll_interval)
                
        except OpenAIError:
            raise
        except Exception as e:
            logger.error(f"Error waiting for run {run_id}: {e}")
            raise OpenAIError(f"Failed to wait for run completion: {e}")
    
    async def get_latest_message(self, thread_id: str) -> Optional[OpenAIMessage]:
        """Get the most recent message from a thread.
        
        Args:
            thread_id: OpenAI thread ID
            
        Returns:
            Latest OpenAI Message or None if thread is empty
            
        Raises:
            OpenAIError: If message retrieval fails
        """
        try:
            messages = await self.client.beta.threads.messages.list(
                thread_id=thread_id,
                limit=1,
                order="desc"
            )
            
            if messages.data:
                return messages.data[0]
            return None
            
        except OpenAIError as e:
            logger.error(f"Failed to get latest message from thread {thread_id}: {e}")
            raise
    
    async def get_thread_messages(
        self,
        thread_id: str,
        limit: int = 100,
        order: str = "asc"
    ) -> list[OpenAIMessage]:
        """Get all messages from a thread.
        
        Args:
            thread_id: OpenAI thread ID
            limit: Maximum number of messages to retrieve (default: 100)
            order: Message order - "asc" or "desc" (default: "asc")
            
        Returns:
            List of OpenAI Messages
            
        Raises:
            OpenAIError: If message retrieval fails
        """
        try:
            messages = await self.client.beta.threads.messages.list(
                thread_id=thread_id,
                limit=limit,
                order=order
            )
            return messages.data
        except OpenAIError as e:
            logger.error(f"Failed to get messages from thread {thread_id}: {e}")
            raise
    
    async def delete_thread(self, thread_id: str) -> bool:
        """Delete a thread.
        
        Args:
            thread_id: OpenAI thread ID
            
        Returns:
            True if deletion was successful
            
        Raises:
            OpenAIError: If thread deletion fails
        """
        try:
            await self.client.beta.threads.delete(thread_id)
            logger.info(f"Deleted thread: {thread_id}")
            return True
        except OpenAIError as e:
            logger.error(f"Failed to delete thread {thread_id}: {e}")
            raise
    
    async def run_assistant_streaming(
        self,
        thread_id: str,
        assistant_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Run the assistant with streaming responses.
        
        Streams the assistant's response as it's generated.
        
        Args:
            thread_id: OpenAI thread ID
            assistant_id: Optional assistant ID (uses default if not provided)
            
        Yields:
            Dictionary with streaming events and data
            
        Raises:
            OpenAIError: If streaming fails
        """
        if not assistant_id:
            assistant = await self.get_or_create_assistant()
            assistant_id = assistant.id
        
        try:
            logger.debug(f"Starting streaming run on thread {thread_id}")
            
            async with self.client.beta.threads.runs.stream(
                thread_id=thread_id,
                assistant_id=assistant_id,
                max_prompt_tokens=self.settings.OPENAI_MAX_TOKENS,
            ) as stream:
                async for event in stream:
                    # Handle different event types
                    event_type = event.event
                    
                    if event_type == "thread.run.created":
                        yield {
                            "type": "run_created",
                            "run_id": event.data.id,
                            "status": event.data.status
                        }
                    
                    elif event_type == "thread.run.in_progress":
                        yield {
                            "type": "run_in_progress",
                            "run_id": event.data.id
                        }
                    
                    elif event_type == "thread.run.completed":
                        usage = self.extract_token_usage(event.data)
                        yield {
                            "type": "run_completed",
                            "run_id": event.data.id,
                            "usage": usage
                        }
                    
                    elif event_type == "thread.message.created":
                        yield {
                            "type": "message_created",
                            "message_id": event.data.id,
                            "role": event.data.role
                        }
                    
                    elif event_type == "thread.message.delta":
                        # Extract text delta from content
                        if event.data.delta and event.data.delta.content:
                            for content in event.data.delta.content:
                                if hasattr(content, 'text') and content.text:
                                    text_delta = content.text.value if hasattr(content.text, 'value') else str(content.text)
                                    yield {
                                        "type": "text_delta",
                                        "delta": text_delta
                                    }
                    
                    elif event_type == "thread.message.completed":
                        yield {
                            "type": "message_completed",
                            "message_id": event.data.id
                        }
                    
                    elif event_type == "thread.run.failed":
                        logger.error(f"Run failed: {event.data.last_error}")
                        yield {
                            "type": "error",
                            "error": str(event.data.last_error)
                        }
                        
        except RateLimitError as e:
            logger.error(f"Rate limit exceeded: {e}")
            yield {
                "type": "error",
                "error": "rate_limit",
                "message": "API rate limit exceeded. Please try again later.",
                "details": str(e)
            }
        except APIConnectionError as e:
            logger.error(f"API connection error: {e}")
            yield {
                "type": "error",
                "error": "connection_error",
                "message": "Failed to connect to OpenAI API. Please check your internet connection.",
                "details": str(e)
            }
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            yield {
                "type": "error",
                "error": "api_error",
                "message": "OpenAI API encountered an error.",
                "details": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error during streaming: {e}")
            yield {
                "type": "error",
                "error": "unexpected_error",
                "message": "An unexpected error occurred.",
                "details": str(e)
            }
    
    async def get_response_non_streaming(
        self,
        thread_id: str,
        user_message: str,
        assistant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get a non-streaming response from the assistant.
        
        Complete workflow: send message, run assistant, wait for completion,
        get response.
        
        Args:
            thread_id: OpenAI thread ID
            user_message: User's message content
            assistant_id: Optional assistant ID (uses default if not provided)
            
        Returns:
            Dictionary with response content, message ID, and token usage
            
        Raises:
            OpenAIError: If any step fails
        """
        try:
            # Send user message
            await self.send_message(thread_id, user_message, role="user")
            
            # Run assistant
            run = await self.run_assistant(thread_id, assistant_id)
            
            # Wait for completion
            completed_run = await self.wait_for_run_completion(thread_id, run.id)
            
            # Get assistant's response
            latest_message = await self.get_latest_message(thread_id)
            
            if not latest_message or latest_message.role != "assistant":
                raise OpenAIError("No assistant response found")
            
            # Extract text content
            content = ""
            if latest_message.content:
                for content_block in latest_message.content:
                    if hasattr(content_block, 'text') and content_block.text:
                        content += content_block.text.value
            
            # Extract token usage
            usage = self.extract_token_usage(completed_run)
            
            return {
                "content": content,
                "message_id": latest_message.id,
                "run_id": completed_run.id,
                "usage": usage,
                "created_at": latest_message.created_at
            }
            
        except RateLimitError as e:
            logger.error(f"Rate limit exceeded: {e}")
            raise OpenAIError(
                "API rate limit exceeded. Please try again later."
            ) from e
        except APIConnectionError as e:
            logger.error(f"API connection error: {e}")
            raise OpenAIError(
                "Failed to connect to OpenAI API. Please check your internet connection."
            ) from e
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise OpenAIError(f"OpenAI API encountered an error: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise OpenAIError(f"An unexpected error occurred: {e}") from e
    
    def extract_token_usage(self, run: Run) -> Dict[str, int]:
        """Extract token usage information from a completed run.
        
        Args:
            run: Completed Run instance
            
        Returns:
            Dictionary with prompt_tokens, completion_tokens, and total_tokens
        """
        usage = run.usage
        if usage:
            return {
                "prompt_tokens": usage.prompt_tokens or 0,
                "completion_tokens": usage.completion_tokens or 0,
                "total_tokens": usage.total_tokens or 0,
            }
        
        # Return zeros if usage information not available
        logger.warning(f"No usage information available for run {run.id}")
        return {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }
    
    async def close(self):
        """Close the OpenAI client and cleanup resources."""
        await self.client.close()
        logger.info("OpenAI service closed")


# Singleton instance management
_openai_service: Optional[OpenAIService] = None


def get_openai_service(settings: Optional[Settings] = None) -> OpenAIService:
    """Get or create OpenAI service singleton.
    
    Args:
        settings: Optional Settings instance (required for first call)
        
    Returns:
        OpenAIService instance
        
    Raises:
        ValueError: If settings not provided on first call
    """
    global _openai_service
    
    if _openai_service is None:
        if settings is None:
            raise ValueError("Settings required to initialize OpenAI service")
        _openai_service = OpenAIService(settings)
    
    return _openai_service
