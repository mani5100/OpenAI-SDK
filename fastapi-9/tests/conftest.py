"""Pytest configuration and shared fixtures."""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Add src to path so we can import the app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    with patch("openai.OpenAI") as mock:
        yield mock


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set required environment variables for testing."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-12345")
    monkeypatch.setenv("OPENAI_DEFAULT_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("OPENAI_DEFAULT_TEMPERATURE", "0.7")
    monkeypatch.setenv("SESSION_TTL_SECONDS", "1800")
    monkeypatch.setenv("SESSION_MAX_TURNS", "20")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")


@pytest.fixture
def test_client(mock_env_vars):
    """Create a FastAPI test client."""
    from fastapi_9.main import app
    
    return TestClient(app)


@pytest.fixture
async def async_test_client(mock_env_vars):
    """Create an async FastAPI test client."""
    from fastapi_9.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_agent_response():
    """Create a mock agent response."""
    return {
        "final_output": "Hello! I'm a helpful assistant.",
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 15,
            "total_tokens": 25,
        }
    }


@pytest.fixture
def mock_agent_manager():
    """Mock AgentManager for testing."""
    with patch("fastapi_9.agent.AgentManager") as mock:
        mock_instance = MagicMock()
        mock_instance.run_chat = AsyncMock(return_value={
            "reply": "Hello! How can I help?",
            "model": "gpt-4o-mini",
            "usage": {"prompt_tokens": 5, "completion_tokens": 10},
        })
        mock.return_value = mock_instance
        yield mock_instance
