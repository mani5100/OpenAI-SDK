"""
Configuration settings for the FastAPI Chatbot application.

This module uses Pydantic Settings for environment variable management
with validation and type checking.
"""

from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings are loaded from .env file or environment variables.
    Required settings will raise a validation error if not provided.
    """
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = Field(
        ...,
        description="OpenAI API key for authentication"
    )
    
    OPENAI_CHAT_MODEL: str = Field(
        default="gpt-4o-mini",
        description="OpenAI chat model to use for the assistant"
    )
    
    OPENAI_ASSISTANT_NAME: str = Field(
        default="Helpful Assistant",
        description="Name for the OpenAI assistant"
    )
    
    OPENAI_ASSISTANT_INSTRUCTIONS: str = Field(
        default="You are a helpful assistant.",
        description="Instructions for the OpenAI assistant behavior"
    )
    
    OPENAI_TEMPERATURE: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for response randomness (0.0 to 2.0)"
    )
    
    OPENAI_MAX_TOKENS: Optional[int] = Field(
        default=None,
        gt=0,
        description="Maximum tokens for responses"
    )
    
    # Database Configuration
    POSTGRES_URL: str = Field(
        ...,
        description="PostgreSQL database connection URL"
    )
    
    # API Configuration
    API_HOST: str = Field(
        default="0.0.0.0",
        description="Host to bind the API server"
    )
    
    API_PORT: int = Field(
        default=8000,
        gt=0,
        lt=65536,
        description="Port to bind the API server"
    )
    
    API_RELOAD: bool = Field(
        default=True,
        description="Enable auto-reload in development"
    )
    
    # CORS Configuration
    CORS_ORIGINS: str = Field(
        default="*",
        description="Allowed CORS origins (comma-separated)"
    )
    
    # Application Configuration
    APP_NAME: str = Field(
        default="OpenAI Chatbot API",
        description="Application name"
    )
    
    APP_VERSION: str = Field(
        default="1.0.0",
        description="Application version"
    )
    
    APP_DESCRIPTION: str = Field(
        default="A FastAPI-based chatbot service using OpenAI Agents SDK with conversation history persistence",
        description="Application description"
    )
    
    # Logging Configuration
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    
    @field_validator("OPENAI_API_KEY")
    @classmethod
    def validate_openai_api_key(cls, v: str) -> str:
        """Validate that OpenAI API key is provided and not placeholder"""
        if not v or v == "your_openai_api_key_here":
            raise ValueError(
                "OPENAI_API_KEY must be set to a valid API key. "
                "Please set it in your .env file or environment variables."
            )
        return v
    
    @field_validator("POSTGRES_URL")
    @classmethod
    def validate_postgres_url(cls, v: str) -> str:
        """Validate that PostgreSQL URL is provided"""
        if not v:
            raise ValueError(
                "POSTGRES_URL must be set. "
                "Please set it in your .env file or environment variables."
            )
        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError(
                "POSTGRES_URL must start with 'postgresql://' or 'postgresql+asyncpg://'"
            )
        return v
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level"""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(
                f"LOG_LEVEL must be one of {valid_levels}, got '{v}'"
            )
        return v_upper
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
    
    def get_cors_origins(self) -> list[str]:
        """Parse CORS origins from comma-separated string"""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


# Create a singleton instance of settings
settings = Settings()


# For backward compatibility with existing code
class Config:
    """Backward compatibility wrapper for existing code"""
    OPENAI_API_KEY = settings.OPENAI_API_KEY
    OPENAI_CHAT_MODEL = settings.OPENAI_CHAT_MODEL
    POSTGRES_URL = settings.POSTGRES_URL
