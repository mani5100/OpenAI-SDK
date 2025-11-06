"""Pydantic schemas for chat API endpoints."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request model for chat message endpoint."""

    message: str = Field(..., min_length=1, description="User message to send to the chatbot")
    thread_id: Optional[str] = Field(None, description="Optional thread ID. If not provided, a new thread will be created")
    stream: bool = Field(False, description="Whether to stream the response using Server-Sent Events")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Hello! Can you help me with Python?",
                    "thread_id": None,
                    "stream": False
                },
                {
                    "message": "What is FastAPI?",
                    "thread_id": "thread_abc123",
                    "stream": True
                }
            ]
        }
    }


class MessageResponse(BaseModel):
    """Response model for a single message."""

    id: str = Field(..., description="Message database ID (UUID)")
    thread_id: str = Field(..., description="Thread database ID (UUID)")
    openai_message_id: Optional[str] = Field(None, description="OpenAI message ID")
    role: str = Field(..., description="Message role (user or assistant)")
    content: str = Field(..., description="Message content")
    prompt_tokens: int = Field(0, description="Number of prompt tokens used")
    completion_tokens: int = Field(0, description="Number of completion tokens used")
    total_tokens: int = Field(0, description="Total tokens used")
    created_at: datetime = Field(..., description="Message creation timestamp")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "2fa7dd66-338d-4f7c-b749-fa6cc358e5a0",
                    "thread_id": "thread_abc123",
                    "openai_message_id": "msg_xyz789",
                    "role": "assistant",
                    "content": "Hello! I'd be happy to help you with Python.",
                    "prompt_tokens": 15,
                    "completion_tokens": 12,
                    "total_tokens": 27,
                    "created_at": "2025-11-06T12:00:00Z"
                }
            ]
        }
    }


class ChatResponse(BaseModel):
    """Response model for non-streaming chat endpoint."""

    thread_id: str = Field(..., description="OpenAI thread ID")
    user_message: MessageResponse = Field(..., description="The user's message that was sent")
    assistant_message: MessageResponse = Field(..., description="The assistant's response")
    total_tokens: int = Field(..., description="Total tokens used in this interaction")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "thread_id": "thread_abc123",
                    "user_message": {
                        "id": 1,
                        "thread_id": "thread_abc123",
                        "role": "user",
                        "content": "Hello!",
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0,
                        "created_at": "2025-11-06T12:00:00Z"
                    },
                    "assistant_message": {
                        "id": 2,
                        "thread_id": "thread_abc123",
                        "role": "assistant",
                        "content": "Hello! How can I help you?",
                        "prompt_tokens": 15,
                        "completion_tokens": 12,
                        "total_tokens": 27,
                        "created_at": "2025-11-06T12:00:01Z"
                    },
                    "total_tokens": 27
                }
            ]
        }
    }


class ThreadResponse(BaseModel):
    """Response model for thread details."""

    id: str = Field(..., description="Thread database ID (UUID)")
    thread_id: str = Field(..., description="OpenAI thread ID")
    message_count: int = Field(0, description="Number of messages in thread")
    total_tokens: int = Field(0, description="Total tokens used across all messages")
    created_at: datetime = Field(..., description="Thread creation timestamp")
    updated_at: datetime = Field(..., description="Thread last update timestamp")
    messages: list[MessageResponse] = Field(default_factory=list, description="List of messages in the thread")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "thread_id": "thread_abc123",
                    "message_count": 4,
                    "total_tokens": 156,
                    "created_at": "2025-11-06T12:00:00Z",
                    "updated_at": "2025-11-06T12:05:00Z",
                    "messages": []
                }
            ]
        }
    }


class ThreadListResponse(BaseModel):
    """Response model for paginated thread list."""

    threads: list[ThreadResponse] = Field(..., description="List of threads")
    total: int = Field(..., description="Total number of threads")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "threads": [],
                    "total": 10,
                    "page": 1,
                    "page_size": 10,
                    "total_pages": 1
                }
            ]
        }
    }
