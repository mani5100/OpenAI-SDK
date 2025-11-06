"""Chat API endpoints for OpenAI chatbot."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ...schemas.chat import (
    ChatRequest,
    ChatResponse,
    MessageResponse,
    ThreadResponse,
    ThreadListResponse,
)
from ...services import ChatService
from ..dependencies import get_db_session


router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)


@router.post(
    "/message",
    response_model=ChatResponse,
    summary="Send a message to the chatbot",
    response_description="Chat response with user message, assistant reply, and token usage",
)
async def send_message(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Send a message to the OpenAI chatbot assistant.
    
    ## Behavior
    - **New Conversation**: If `thread_id` is not provided, a new conversation thread is automatically created
    - **Existing Conversation**: If `thread_id` is provided, the message is added to that conversation
    - **Non-Streaming**: By default (`stream=False`), returns the complete response immediately
    - **Streaming**: If `stream=True`, returns real-time response using Server-Sent Events (SSE)
    
    ## Response
    - Contains both the user message and assistant response
    - Includes token usage statistics (prompt, completion, and total tokens)
    - All messages are persisted to PostgreSQL database
    
    Args:
        request: Chat request with message, optional thread_id, and stream flag
        db: Database session (injected)
        
    Returns:
        ChatResponse: User message and assistant response with token counts
        
    Raises:
        HTTPException: 404 if thread_id provided but not found
        HTTPException: 500 if OpenAI API error occurs
    """
    logger.info(
        "Chat message request received",
        extra={
            "extra_fields": {
                "has_thread_id": request.thread_id is not None,
                "thread_id": request.thread_id,
                "stream": request.stream,
                "message_length": len(request.message),
            }
        },
    )
    
    # Create chat service with db session
    chat_service = ChatService(db)
    
    try:
        # Handle streaming responses
        if request.stream:
            logger.info("Processing streaming request")
            return await send_message_streaming(request, chat_service)
        
        # Auto-create thread if not provided
        thread_id = request.thread_id
        if thread_id is None:
            logger.info("Auto-creating new thread")
            thread_id = await chat_service.create_thread()
            logger.info(f"New thread created", extra={"extra_fields": {"thread_id": thread_id}})
        
        # Send message and get response (non-streaming)
        logger.info(
            "Sending message to OpenAI",
            extra={"extra_fields": {"thread_id": thread_id}}
        )
        user_msg, assistant_msg = await chat_service.send_message_non_streaming(
            thread_id=thread_id,
            message=request.message
        )
        
        # Convert database models to Pydantic responses
        user_response = MessageResponse.model_validate(user_msg)
        assistant_response = MessageResponse.model_validate(assistant_msg)
        
        logger.info(
            "Chat message processed successfully",
            extra={
                "extra_fields": {
                    "thread_id": thread_id,
                    "total_tokens": assistant_msg.total_tokens,
                    "prompt_tokens": assistant_msg.prompt_tokens,
                    "completion_tokens": assistant_msg.completion_tokens,
                }
            },
        )
        
        return ChatResponse(
            thread_id=thread_id,
            user_message=user_response,
            assistant_message=assistant_response,
            total_tokens=assistant_msg.total_tokens
        )
        
    except Exception as e:
        logger.error(
            f"Error processing chat message: {str(e)}",
            extra={
                "extra_fields": {
                    "error_type": type(e).__name__,
                    "thread_id": request.thread_id,
                }
            },
            exc_info=True,
        )
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=f"Thread not found: {thread_id}")
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")


async def send_message_streaming(
    request: ChatRequest,
    chat_service: ChatService,
):
    """
    Send a message with streaming response using Server-Sent Events.
    
    Args:
        request: Chat request with message and optional thread_id
        chat_service: Chat service instance
        
    Returns:
        StreamingResponse: SSE stream of chat events
    """
    logger.info(
        "Starting streaming chat response",
        extra={
            "extra_fields": {
                "has_thread_id": request.thread_id is not None,
                "thread_id": request.thread_id,
            }
        },
    )
    
    # Auto-create thread if not provided
    thread_id = request.thread_id
    if thread_id is None:
        thread_id = await chat_service.create_thread()
        logger.info(
            "Thread auto-created for streaming",
            extra={"extra_fields": {"thread_id": thread_id}}
        )
    
    async def event_generator():
        """Generate Server-Sent Events for streaming response."""
        try:
            # Send initial event with thread_id
            yield f"event: thread_created\ndata: {{'thread_id': '{thread_id}'}}\n\n"
            
            logger.debug("Streaming response events", extra={"extra_fields": {"thread_id": thread_id}})
            
            # Stream assistant response
            async for event in chat_service.send_message_streaming(thread_id, request.message):
                event_type = event.get("event", "message")
                data = event.get("data", {})
                
                # Format as SSE
                yield f"event: {event_type}\ndata: {data}\n\n"
            
            # Send completion event
            yield "event: done\ndata: {}\n\n"
            
            logger.info(
                "Streaming response completed",
                extra={"extra_fields": {"thread_id": thread_id}}
            )
            
        except Exception as e:
            logger.error(
                f"Error in streaming response: {str(e)}",
                extra={
                    "extra_fields": {
                        "error_type": type(e).__name__,
                        "thread_id": thread_id,
                    }
                },
                exc_info=True,
            )
            error_msg = str(e)
            yield f"event: error\ndata: {{'error': '{error_msg}'}}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@router.get(
    "/threads/{thread_id}",
    response_model=ThreadResponse,
    summary="Get conversation thread by ID",
    response_description="Thread details with complete message history",
)
async def get_thread(
    thread_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Retrieve a conversation thread with its complete message history.
    
    ## Returns
    - Thread metadata (ID, creation time, message count, total tokens)
    - Complete chronological list of all messages in the conversation
    - Token usage for each message
    
    ## Use Cases
    - Review conversation history
    - Analyze token usage
    - Export conversation data
    
    Args:
        thread_id: Unique identifier for the conversation thread
        db: Database session (injected)
        
    Returns:
        ThreadResponse: Thread details with all messages
        
    Raises:
        HTTPException: 404 if thread not found
        HTTPException: 500 if retrieval fails
    """
    logger.info(
        "Retrieving thread details",
        extra={"extra_fields": {"thread_id": thread_id}}
    )
    
    chat_service = ChatService(db)
    
    try:
        thread = await chat_service.get_thread(thread_id)
        if not thread:
            logger.warning(
                "Thread not found",
                extra={"extra_fields": {"thread_id": thread_id}}
            )
            raise HTTPException(status_code=404, detail=f"Thread not found: {thread_id}")
        
        # Get messages for this thread
        messages = await chat_service.get_thread_messages(thread_id)
        
        logger.info(
            "Thread retrieved successfully",
            extra={
                "extra_fields": {
                    "thread_id": thread_id,
                    "message_count": len(messages),
                }
            }
        )
        
        # Convert to response model
        message_responses = [MessageResponse.model_validate(msg) for msg in messages]
        return ThreadResponse(
            id=thread.id,
            thread_id=thread.openai_thread_id,
            message_count=thread.message_count,
            total_tokens=thread.total_tokens,
            created_at=thread.created_at,
            updated_at=thread.updated_at,
            messages=message_responses
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        # Invalid UUID format or thread not found
        logger.warning(
            f"Invalid thread ID format: {str(e)}",
            extra={"extra_fields": {"thread_id": thread_id}}
        )
        raise HTTPException(status_code=404, detail=f"Thread not found: {thread_id}")
    except Exception as e:
        logger.error(
            f"Error retrieving thread: {str(e)}",
            extra={
                "extra_fields": {
                    "error_type": type(e).__name__,
                    "thread_id": thread_id,
                }
            },
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Error retrieving thread: {str(e)}")


@router.get(
    "/threads",
    response_model=ThreadListResponse,
    summary="List all conversation threads",
    response_description="Paginated list of conversation threads",
)
async def list_threads(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    db: AsyncSession = Depends(get_db_session),
):
    """
    List all conversation threads with pagination support.
    
    ## Pagination
    - Default: 10 threads per page
    - Maximum: 100 threads per page
    - Pages are 1-indexed (first page is 1, not 0)
    
    ## Response
    - Thread metadata only (messages not included for performance)
    - Total count of all threads
    - Current page and total pages
    - Use `GET /chat/threads/{thread_id}` to get full message history
    
    """
    logger.info(
        "Listing threads",
        extra={"extra_fields": {"page": page, "page_size": page_size}}
    )
    
    chat_service = ChatService(db)
    
    try:
        # Get paginated threads
        threads, total = await chat_service.list_threads(skip=(page - 1) * page_size, limit=page_size)
        
        logger.info(
            "Threads retrieved successfully",
            extra={
                "extra_fields": {
                    "total_threads": total,
                    "returned_count": len(threads),
                    "page": page,
                }
            }
        )
        
        # Convert to response models
        thread_responses = []
        for thread in threads:
            thread_responses.append(ThreadResponse(
                id=thread.id,
                thread_id=thread.openai_thread_id,
                message_count=thread.message_count,
                total_tokens=thread.total_tokens,
                created_at=thread.created_at,
                updated_at=thread.updated_at,
                messages=[]  # Don't include messages in list view
            ))
        
        # Calculate total pages
        total_pages = (total + page_size - 1) // page_size
        
        return ThreadListResponse(
            threads=thread_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(
            f"Error listing threads: {str(e)}",
            extra={"extra_fields": {"error_type": type(e).__name__}},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Error listing threads: {str(e)}")


@router.delete(
    "/threads/{thread_id}",
    summary="Delete a conversation thread",
    response_description="Deletion confirmation message",
)
async def delete_thread(
    thread_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Delete a conversation thread and all its messages.
    
    ## Behavior
    - Deletes the thread from both OpenAI and PostgreSQL database
    - Cascade deletes all associated messages
    - Operation is irreversible
    
    ## Returns
    - Success confirmation with thread ID
    - Returns 404 if thread doesn't exist
    
    Args:
        thread_id: Unique identifier for the conversation thread to delete
        db: Database session (injected)
        
    Returns:
        dict: Success confirmation with thread_id
        
    Raises:
        HTTPException: 404 if thread not found
        HTTPException: 500 if deletion fails
    """
    logger.info(
        "Deleting thread",
        extra={"extra_fields": {"thread_id": thread_id}}
    )
    
    chat_service = ChatService(db)
    
    try:
        # Delete thread from both OpenAI and database
        success = await chat_service.delete_thread(thread_id)
        
        if not success:
            logger.warning(
                "Thread not found for deletion",
                extra={"extra_fields": {"thread_id": thread_id}}
            )
            raise HTTPException(status_code=404, detail=f"Thread not found: {thread_id}")
        
        logger.info(
            "Thread deleted successfully",
            extra={"extra_fields": {"thread_id": thread_id}}
        )
        
        return {
            "success": True,
            "message": f"Thread {thread_id} deleted successfully",
            "thread_id": thread_id
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        # Invalid UUID format or thread not found
        logger.warning(
            f"Invalid thread ID format: {str(e)}",
            extra={"extra_fields": {"thread_id": thread_id}}
        )
        raise HTTPException(status_code=404, detail=f"Thread not found: {thread_id}")
    except Exception as e:
        logger.error(
            f"Error deleting thread: {str(e)}",
            extra={
                "extra_fields": {
                    "error_type": type(e).__name__,
                    "thread_id": thread_id,
                }
            },
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Error deleting thread: {str(e)}")
