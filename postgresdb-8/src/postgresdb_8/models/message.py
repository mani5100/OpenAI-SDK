"""
Message model for storing conversation messages.

This model stores individual messages within conversation threads,
including role, content, and token usage information.
"""

import enum

from sqlalchemy import Enum, ForeignKey, Integer, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class MessageRole(str, enum.Enum):
    """Enum for message roles."""
    USER = "user"
    ASSISTANT = "assistant"


class Message(Base, TimestampMixin):
    """
    Message model representing a single message in a conversation.
    
    Stores individual messages with role (user/assistant), content,
    and token usage information.
    
    Attributes:
        id (str): UUID primary key (inherited from TimestampMixin)
        thread_id (str): Foreign key to conversation_threads
        role (MessageRole): Message role (user or assistant)
        content (str): Message content text
        created_at (datetime): Message creation timestamp (inherited)
        prompt_tokens (int): Tokens used in the prompt
        completion_tokens (int): Tokens used in the completion
        updated_at (datetime): Last update timestamp (inherited)
    """
    
    __tablename__ = "messages"
    
    thread_id: Mapped[str] = mapped_column(
        ForeignKey("conversation_threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to conversation_threads table"
    )
    
    role: Mapped[MessageRole] = mapped_column(
        Enum(MessageRole, native_enum=False, length=20),
        nullable=False,
        comment="Message role: user or assistant"
    )
    
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Message content text"
    )
    
    prompt_tokens: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of tokens in the prompt"
    )
    
    completion_tokens: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of tokens in the completion"
    )
    
    # Relationship to thread
    thread: Mapped["ConversationThread"] = relationship(
        "ConversationThread",
        back_populates="messages"
    )
    
    @property
    def total_tokens(self) -> int:
        """Calculate total tokens used in this message."""
        return self.prompt_tokens + self.completion_tokens
    
    def __repr__(self) -> str:
        """String representation of the Message."""
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return (
            f"<Message("
            f"id={self.id}, "
            f"thread_id={self.thread_id}, "
            f"role={self.role.value}, "
            f"content='{content_preview}', "
            f"total_tokens={self.total_tokens}"
            f")>"
        )


# Create index on thread_id for faster lookups
__table_args__ = (
    Index('ix_messages_thread_id', 'thread_id'),
)
