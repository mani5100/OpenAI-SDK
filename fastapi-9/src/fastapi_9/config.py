"""Configuration management for the FastAPI OpenAI Agent SDK application."""

import logging
from typing import Optional

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra environment variables
    )

    # OpenAI API Configuration
    openai_api_key: str
    openai_default_model: str = "gpt-4o-mini"
    openai_default_temperature: float = 0.7
    openai_timeout_seconds: int = 30

    # Session Configuration
    session_ttl_seconds: int = 1800  # 30 minutes
    session_max_turns: int = 20  # Max number of user+assistant message pairs

    # Logging Configuration
    log_level: str = "INFO"
    debug_mode: bool = False  # Enable full content logging when True

    # FastAPI Configuration
    app_title: str = "Conversation AI Agent API"
    app_version: str = "0.1.0"
    app_description: str = "REST API for conversational AI powered by OpenAI Agents SDK"

    def get_logger(self, name: str) -> logging.Logger:
        """Create a configured logger instance."""
        logger = logging.getLogger(name)
        log_level = getattr(logging, self.log_level.upper(), logging.INFO)
        logger.setLevel(log_level)
        return logger


def load_config() -> Config:
    """Load and validate configuration from environment."""
    try:
        config = Config()
        return config
    except Exception as e:
        raise RuntimeError(f"Failed to load configuration: {e}") from e


# Global config instance (lazy-loaded)
_config: Optional[Config] = None


def get_config() -> Config:
    """Get or create the global config instance."""
    global _config
    if _config is None:
        _config = load_config()
    return _config
