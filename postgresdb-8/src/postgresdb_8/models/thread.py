"""
ConversationThread model for storing conversation threads.

This model stores information about conversation threads,
including the OpenAI thread ID and metadata.
"""

from datetime import datetime

from sqlalchemy import Integer, String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class ConversationThread(Base, TimestampMixin):
    """
    ConversationThread model representing a conversation thread.
    
    Stores information about conversation threads with OpenAI,
    including thread metadata and message tracking.
    
    Attributes:
        id (str): UUID primary key (inherited from TimestampMixin)
        openai_thread_id (str): OpenAI thread identifier (unique)
        created_at (datetime): Thread creation timestamp (inherited)
        last_activity_at (datetime): Last activity timestamp
        message_count (int): Total number of messages in thread
        total_tokens (int): Total tokens used in thread
        updated_at (datetime): Last update timestamp (inherited)
    """
    
    __tablename__ = "conversation_threads"
    
    openai_thread_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="OpenAI thread identifier"
    )
    
    last_activity_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
        comment="Timestamp of last activity in the thread"
    )
    
    message_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Total number of messages in the thread"
    )
    
    total_tokens: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Total tokens used across all messages"
    )
    
    # Relationship to messages
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="thread",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        """String representation of the ConversationThread."""
        return (
            f"<ConversationThread("
            f"id={self.id}, "
            f"openai_thread_id={self.openai_thread_id}, "
            f"message_count={self.message_count}, "
            f"total_tokens={self.total_tokens}"
            f")>"
        )
    
    def update_activity(self, token_count: int = 0) -> None:
        """
        Update thread activity timestamp and token count.
        
        Args:
            token_count: Number of tokens to add to total
        """
        self.last_activity_at = datetime.utcnow()
        self.message_count += 1
        self.total_tokens += token_count


# Create index on openai_thread_id for faster lookups
__table_args__ = (
    Index('ix_conversation_threads_openai_thread_id', 'openai_thread_id'),
)
