## Relevant Files

- `src/fastapi_9/main.py` - FastAPI app entry point, route definitions, and server startup.
- `src/fastapi_9/config.py` - Environment configuration, default values, and validation.
- `src/fastapi_9/models.py` - Pydantic request/response models for chat endpoint.
- `src/fastapi_9/agent.py` - OpenAI Agent initialization, session management, and wrapper logic.
- `src/fastapi_9/session_store.py` - In-memory session context manager with TTL and message bounds.
- `src/fastapi_9/errors.py` - Custom exception classes and error handling utilities.
- `src/fastapi_9/logging.py` - Structured logging setup, correlation ID generation, and formatters.
- `src/fastapi_9/utils.py` - Helper functions (token estimation, latency measurement, etc.).
- `src/fastapi_9/__init__.py` - Package initialization and version info.
- `tests/test_chat_endpoint.py` - Unit tests for POST /api/agent/chat.
- `tests/test_session_store.py` - Unit tests for session context management.
- `tests/test_error_handling.py` - Unit tests for error scenarios.
- `tests/test_config.py` - Unit tests for configuration loading and defaults.
- `tests/conftest.py` - Pytest fixtures (FastAPI test client, mock OpenAI client, etc.).
- `.env.example` - Example environment variables.
- `.env` - Local development environment file (git-ignored).
- `pyproject.toml` - Project metadata and uv dependencies (FastAPI, uvicorn, openai-agents, pydantic, etc.).
- `README.md` - Setup, usage, and API examples.

### Notes

- Use `pytest` for unit tests; run with `uv run pytest [optional/path/to/test]`.
- Use `uv run` to execute Python commands in the configured environment.
- Session store uses in-memory dict with background cleanup task for TTL eviction.
- Keep sensitive data (API keys) out of logs; log only sizes/timings.
- FastAPI auto-generates `/docs` (Swagger) and `/redoc` (ReDoc) endpoints.

## Tasks

- [x] 1.0 Project setup and dependencies
  - [x] 1.1 Update `pyproject.toml` with dependencies: fastapi, uvicorn, openai-agents, pydantic, python-dotenv, pytest, pytest-asyncio, httpx (for async test client).
  - [x] 1.2 Create `src/fastapi_9/config.py` with Config class: read env vars (OPENAI_API_KEY, OPENAI_DEFAULT_MODEL, OPENAI_DEFAULT_TEMPERATURE, OPENAI_TIMEOUT_SECONDS, SESSION_TTL_SECONDS, SESSION_MAX_TURNS, LOG_LEVEL).
  - [x] 1.3 Create `.env.example` with all required and optional env vars and default values.
  - [x] 1.4 Install dependencies using `uv sync`.
  - [x] 1.5 Set up pytest and create `tests/` directory structure with `conftest.py`.

- [x] 2.0 FastAPI app scaffolding and configuration
  - [x] 2.1 Create `src/fastapi_9/main.py` with FastAPI app instance, root route, and health check endpoint.
  - [x] 2.2 Configure FastAPI with title, version, description, and OpenAPI info for Swagger/Redoc.
  - [x] 2.3 Set up request/response logging middleware (log size, correlation ID, timing, but not content).
  - [x] 2.4 Create `src/fastapi_9/logging.py` with structured logging setup, correlation ID generator, and custom formatters.
  - [x] 2.5 Add shutdown and startup event handlers in main.py for graceful session cleanup.

- [ ] 3.0 Chat API endpoint `POST /api/agent/chat`
  - [ ] 3.1 Create `src/fastapi_9/models.py` with Pydantic models: ChatRequest (message, session_id?, model?, system_prompt?, temperature?), ChatResponse (reply, model, usage?, latency_ms, session_id?, truncated_history).
  - [ ] 3.2 Define `POST /api/agent/chat` endpoint in main.py that accepts ChatRequest and returns ChatResponse.
  - [ ] 3.3 Implement message validation and request/response schema in Swagger (add example requests/responses).
  - [ ] 3.4 Measure endpoint latency from request start to response completion; include in ChatResponse.
  - [ ] 3.5 Test endpoint with valid/invalid inputs locally and verify Swagger examples work.

- [ ] 4.0 In-memory session context (TTL + max turns + truncation flag)
  - [ ] 4.1 Create `src/fastapi_9/session_store.py` with SessionStore class: maintain dict[session_id] -> list of messages, last_accessed timestamp.
  - [ ] 4.2 Implement get_session(session_id) and add_message(session_id, role, content) methods.
  - [ ] 4.3 Implement TTL eviction: background task runs periodically, removes sessions inactive > SESSION_TTL_SECONDS.
  - [ ] 4.4 Implement max turn bounds: when session messages exceed SESSION_MAX_TURNS, drop oldest turns and set truncated_history=true.
  - [ ] 4.5 Add session cleanup on app shutdown.
  - [ ] 4.6 Write unit tests for session store (TTL, max turns, truncation flag).

- [ ] 5.0 OpenAI SDK integration and request parameterization
  - [ ] 5.1 Create `src/fastapi_9/agent.py` with AgentManager class wrapping openai-agents SDK: Agent, Runner, Session.
  - [ ] 5.2 Initialize OpenAI Agent with instructions="You are a helpful assistant." and system_prompt override support.
  - [ ] 5.3 Implement run_chat(message, session_id?, model?, temperature?, system_prompt?) that: retrieves session history (if session_id provided), calls Runner.run_sync() or async equivalent, updates session, returns result.
  - [ ] 5.4 Support model and temperature parameter overrides per request; fallback to env defaults.
  - [ ] 5.5 Extract usage info (tokens) from Agent result if available; store in response.
  - [ ] 5.6 Wire AgentManager into the /api/agent/chat endpoint in main.py.
  - [ ] 5.7 Test agent with real OpenAI API (mock or sandbox key if available).

- [ ] 6.0 Error handling and HTTP response mapping
  - [ ] 6.1 Create `src/fastapi_9/errors.py` with custom exception classes: InvalidRequestError, OpenAITimeoutError, OpenAIRateLimitError, OpenAIServiceError.
  - [ ] 6.2 Map OpenAI SDK exceptions to HTTP responses: 400 (invalid), 408 (timeout), 429 (rate limit with retry_after), 502/503 (service).
  - [ ] 6.3 Add FastAPI exception handlers for each custom error; return stable error response shape: {error: {code: str, message: str, retry_after?: int}}.
  - [ ] 6.4 Handle edge cases: empty message, missing OPENAI_API_KEY, invalid model name.
  - [ ] 6.5 Log errors with correlation ID and error code; avoid logging user message content by default.
  - [ ] 6.6 Write unit tests for error scenarios (timeout, rate limit, service error).

- [ ] 7.0 Observability (structured logging, latency measurement, correlation id)
  - [ ] 7.1 Implement correlation ID middleware in main.py: generate UUID per request, inject into response headers, store in context for logging.
  - [ ] 7.2 Log request start (method, path, correlation_id) and end (status, latency_ms, request_size, response_size).
  - [ ] 7.3 Use structured logging (JSON format or similar); avoid logging full message/reply content by default (log sizes instead).
  - [ ] 7.4 Add debug mode env var to optionally enable full content logging for troubleshooting.
  - [ ] 7.5 Measure and log OpenAI latency separately from total endpoint latency.
  - [ ] 7.6 Write unit tests for logging output and correlation ID propagation.

- [ ] 8.0 API documentation and examples (Swagger/Redoc)
  - [ ] 8.1 Ensure ChatRequest/ChatResponse models have proper docstrings and field descriptions.
  - [ ] 8.2 Add FastAPI OpenAPI examples in endpoint docstring: example request body, example response (successful and error).
  - [ ] 8.3 Verify `/docs` (Swagger) and `/redoc` endpoints render correctly.
  - [ ] 8.4 Add example curl commands and Python client code to README.md for quick integration.
  - [ ] 8.5 Document all env vars, defaults, and override behavior in README.md.

- [ ] 9.0 Local run instructions and environment configuration
  - [ ] 9.1 Document how to set OPENAI_API_KEY locally (Windows PowerShell: $env:OPENAI_API_KEY = "sk-...").
  - [ ] 9.2 Create `.env` file locally (git-ignored) with sample values; document in README.
  - [ ] 9.3 Add startup command: `uv run uvicorn src.fastapi_9.main:app --reload --host 0.0.0.0 --port 8000`.
  - [ ] 9.4 Document how to run tests: `uv run pytest` or `uv run pytest -v tests/`.
  - [ ] 9.5 Add troubleshooting section to README: common errors (missing API key, rate limits, timeouts).
  - [ ] 9.6 Verify local run works end-to-end on Windows PowerShell; document any platform-specific quirks.
  - [ ] 9.7 Add requirements verification step: curl or Python test script to verify API is reachable.
