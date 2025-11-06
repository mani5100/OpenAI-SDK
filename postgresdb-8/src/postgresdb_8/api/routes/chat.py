"""Chat API endpoints for OpenAI chatbot."""

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


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Send a message to the chatbot.
    
    If `stream=False` (default), returns complete response.
    If `stream=True`, returns Server-Sent Events stream.
    If `thread_id` is not provided, creates new thread automatically.
    
    Args:
        request: Chat request with message, optional thread_id, and stream flag
        db: Database session (injected)
        
    Returns:
        ChatResponse: User message and assistant response with token counts
        
    Raises:
        HTTPException: 404 if thread_id provided but not found
        HTTPException: 500 if OpenAI API error occurs
    """
    # Create chat service with db session
    chat_service = ChatService(db)
    
    try:
        # Handle streaming responses
        if request.stream:
            return await send_message_streaming(request, chat_service)
        
        # Auto-create thread if not provided
        thread_id = request.thread_id
        if thread_id is None:
            thread_id = await chat_service.create_thread()
        
        # Send message and get response (non-streaming)
        user_msg, assistant_msg = await chat_service.send_message_non_streaming(
            thread_id=thread_id,
            message=request.message
        )
        
        # Convert database models to Pydantic responses
        user_response = MessageResponse.model_validate(user_msg)
        assistant_response = MessageResponse.model_validate(assistant_msg)
        
        return ChatResponse(
            thread_id=thread_id,
            user_message=user_response,
            assistant_message=assistant_response,
            total_tokens=assistant_msg.total_tokens
        )
        
    except Exception as e:
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
    # Auto-create thread if not provided
    thread_id = request.thread_id
    if thread_id is None:
        thread_id = await chat_service.create_thread()
    
    async def event_generator():
        """Generate Server-Sent Events for streaming response."""
        try:
            # Send initial event with thread_id
            yield f"event: thread_created\ndata: {{'thread_id': '{thread_id}'}}\n\n"
            
            # Stream assistant response
            async for event in chat_service.send_message_streaming(thread_id, request.message):
                event_type = event.get("event", "message")
                data = event.get("data", {})
                
                # Format as SSE
                yield f"event: {event_type}\ndata: {data}\n\n"
            
            # Send completion event
            yield "event: done\ndata: {}\n\n"
            
        except Exception as e:
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


@router.get("/threads/{thread_id}", response_model=ThreadResponse)
async def get_thread(
    thread_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get thread details and message history.
    
    Args:
        thread_id: OpenAI thread ID
        db: Database session (injected)
        
    Returns:
        ThreadResponse: Thread details with all messages
        
    Raises:
        HTTPException: 404 if thread not found
    """
    chat_service = ChatService(db)
    
    try:
        # Get thread from database
        thread = await chat_service.database_service.get_thread(thread_id)
        if thread is None:
            raise HTTPException(status_code=404, detail=f"Thread not found: {thread_id}")
        
        # Get message history
        messages = await chat_service.get_thread_history(thread_id)
        
        # Convert to response models
        message_responses = [MessageResponse.model_validate(msg) for msg in messages]
        
        return ThreadResponse(
            id=thread.id,
            thread_id=thread.thread_id,
            message_count=thread.message_count,
            total_tokens=thread.total_tokens,
            created_at=thread.created_at,
            updated_at=thread.updated_at,
            messages=message_responses
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving thread: {str(e)}")


@router.get("/threads", response_model=ThreadListResponse)
async def list_threads(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    db: AsyncSession = Depends(get_db_session),
):
    """
    List all threads with pagination.
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page (1-100)
        db: Database session (injected)
        
    Returns:
        ThreadListResponse: Paginated list of threads
    """
    chat_service = ChatService(db)
    
    try:
        # Get paginated threads
        threads, total = await chat_service.list_threads(skip=(page - 1) * page_size, limit=page_size)
        
        # Convert to response models
        thread_responses = []
        for thread in threads:
            thread_responses.append(ThreadResponse(
                id=thread.id,
                thread_id=thread.thread_id,
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
        raise HTTPException(status_code=500, detail=f"Error listing threads: {str(e)}")


@router.delete("/threads/{thread_id}")
async def delete_thread(
    thread_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Delete a thread and all its messages.
    
    Args:
        thread_id: OpenAI thread ID
        db: Database session (injected)
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: 404 if thread not found
        HTTPException: 500 if deletion fails
    """
    chat_service = ChatService(db)
    
    try:
        # Delete thread from both OpenAI and database
        success = await chat_service.delete_thread(thread_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Thread not found: {thread_id}")
        
        return {
            "success": True,
            "message": f"Thread {thread_id} deleted successfully",
            "thread_id": thread_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting thread: {str(e)}")
