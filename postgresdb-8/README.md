# OpenAI Chatbot API

A production-ready FastAPI-based chatbot service using OpenAI Agents SDK with PostgreSQL for conversation history persistence.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.121.0-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Features

- 🤖 **OpenAI Integration** - Leverages OpenAI Agents SDK for intelligent conversations
- 💾 **Persistent Storage** - PostgreSQL database for conversation history and message tracking
- 🔄 **Streaming Support** - Real-time response streaming via Server-Sent Events (SSE)
- 📊 **Token Tracking** - Comprehensive token usage logging for cost management
- 🛡️ **Error Handling** - Global error handler with custom exceptions
- 📝 **Structured Logging** - JSON-formatted logs with request ID tracking
- 🏥 **Health Monitoring** - Kubernetes-compatible health check endpoints
- 📚 **API Documentation** - Auto-generated Swagger UI and ReDoc documentation
- 🔍 **Request Tracing** - Request ID tracking across all operations
- ⚡ **Async/Await** - Fully asynchronous for high performance

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [API Endpoints](#api-endpoints)
- [Usage Examples](#usage-examples)
- [Testing](#testing)
- [Deployment](#deployment)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

## Prerequisites

- **Python 3.11+** - [Download Python](https://www.python.org/downloads/)
- **PostgreSQL 13+** - [Download PostgreSQL](https://www.postgresql.org/download/)
- **OpenAI API Key** - [Get API Key](https://platform.openai.com/api-keys)
- **uv** (recommended) - Fast Python package installer: `pip install uv`

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/mani5100/OpenAI-SDK.git
cd postgresdb-8
```

### 2. Create Virtual Environment

```bash
# Using uv (recommended)
uv venv

# Or using Python venv
python -m venv .venv
```

### 3. Activate Virtual Environment

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

### 4. Install Dependencies

```bash
# Using uv (faster)
uv pip install -r requirements.txt

# Or using pip
pip install -r requirements.txt
```

## Configuration

### 1. Environment Variables

Create a `.env` file in the project root:

```bash
# Application Settings
APP_NAME="OpenAI Chatbot API"
APP_VERSION="1.0.0"
APP_ENV="development"
LOG_LEVEL="INFO"
LOG_JSON="true"

# Database Configuration
DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/chatbot_db"

# OpenAI Configuration
OPENAI_API_KEY="sk-your-openai-api-key-here"
OPENAI_MODEL="gpt-4o-mini"
OPENAI_MAX_TOKENS="1000"
OPENAI_TEMPERATURE="1.0"
OPENAI_ASSISTANT_NAME="Python Expert Assistant"
OPENAI_ASSISTANT_INSTRUCTIONS="You are a helpful Python programming assistant."

# CORS Configuration (comma-separated)
CORS_ORIGINS="http://localhost:3000,http://localhost:8080"
```

### 2. Configuration File

Settings are managed via `src/postgresdb_8/config/settings.py` using Pydantic Settings.

**Key Configuration Options:**

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4o-mini` |
| `DATABASE_URL` | PostgreSQL connection string | - |
| `LOG_LEVEL` | Logging level | `INFO` |
| `LOG_JSON` | Enable JSON logging | `true` |

## Database Setup

### 1. Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE chatbot_db;

# Exit PostgreSQL
\q
```

### 2. Run Migrations

```bash
# Initialize Alembic (already done)
# alembic init alembic

# Generate migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head
```

### 3. Verify Tables

```bash
psql -U postgres -d chatbot_db -c "\dt"
```

Expected tables:
- `conversation_threads` - Stores conversation threads
- `messages` - Stores individual messages
- `alembic_version` - Migration version tracking

## Running the Application

### Development Mode

```bash
# Using uvicorn with auto-reload
uvicorn src.postgresdb_8.main:app --reload --host 0.0.0.0 --port 8000

# Or using uv
uv run uvicorn src.postgresdb_8.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
# Using Gunicorn with Uvicorn workers
gunicorn src.postgresdb_8.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### Access Points

- **API Root**: http://localhost:8000/
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Chat Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat/message` | Send a message to the chatbot |
| `GET` | `/chat/threads/{thread_id}` | Get thread details with messages |
| `GET` | `/chat/threads` | List all threads (paginated) |
| `DELETE` | `/chat/threads/{thread_id}` | Delete a thread and its messages |

### Health Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Comprehensive health check |
| `GET` | `/health/live` | Liveness probe (Kubernetes) |
| `GET` | `/health/ready` | Readiness probe (Kubernetes) |

## Usage Examples

### 1. Send a Message (New Thread)

```bash
curl -X POST "http://localhost:8000/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello! Can you help me with Python?",
    "stream": false
  }'
```

**Response:**
```json
{
  "thread_id": "thread_abc123",
  "user_message": {
    "id": 1,
    "thread_id": "thread_abc123",
    "role": "user",
    "content": "Hello! Can you help me with Python?",
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0,
    "created_at": "2025-11-07T12:00:00Z"
  },
  "assistant_message": {
    "id": 2,
    "thread_id": "thread_abc123",
    "role": "assistant",
    "content": "Hello! I'd be happy to help you with Python...",
    "prompt_tokens": 25,
    "completion_tokens": 50,
    "total_tokens": 75,
    "created_at": "2025-11-07T12:00:01Z"
  },
  "total_tokens": 75
}
```

### 2. Send a Message (Existing Thread)

```bash
curl -X POST "http://localhost:8000/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are list comprehensions?",
    "thread_id": "thread_abc123",
    "stream": false
  }'
```

### 3. Stream Response (SSE)

```bash
curl -X POST "http://localhost:8000/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain decorators",
    "stream": true
  }'
```

**SSE Response:**
```
event: thread_created
data: {'thread_id': 'thread_xyz789'}

event: text_delta
data: {"delta": "Decorators"}

event: text_delta
data: {"delta": " are a powerful"}

event: done
data: {}
```

### 4. Get Thread History

```bash
curl "http://localhost:8000/chat/threads/thread_abc123"
```

### 5. List All Threads

```bash
# Get first page (10 threads)
curl "http://localhost:8000/chat/threads?page=1&page_size=10"

# Get second page
curl "http://localhost:8000/chat/threads?page=2&page_size=10"
```

### 6. Delete Thread

```bash
curl -X DELETE "http://localhost:8000/chat/threads/thread_abc123"
```

### 7. Health Check

```bash
# Comprehensive health check
curl "http://localhost:8000/health"

# Liveness probe
curl "http://localhost:8000/health/live"

# Readiness probe
curl "http://localhost:8000/health/ready"
```

## Testing

### Run Unit Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/postgresdb_8 --cov-report=html

# Run specific test file
pytest tests/test_chat_service.py

# Run with verbose output
pytest -v
```

### Run Integration Tests

```bash
# Test API endpoints
uv run python test_api_endpoints.py
```

### Manual Testing with Swagger UI

1. Start the application
2. Navigate to http://localhost:8000/docs
3. Use the interactive "Try it out" feature
4. Test all endpoints with example data

## Deployment

### Docker Deployment

**1. Build Docker Image:**

```bash
docker build -t openai-chatbot-api .
```

**2. Run Container:**

```bash
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql+asyncpg://user:pass@db:5432/chatbot_db" \
  -e OPENAI_API_KEY="sk-your-api-key" \
  --name chatbot-api \
  openai-chatbot-api
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: chatbot_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:password@db:5432/chatbot_db
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    depends_on:
      - db
    command: uvicorn src.postgresdb_8.main:app --host 0.0.0.0 --port 8000

volumes:
  postgres_data:
```

**Run with Docker Compose:**

```bash
docker-compose up -d
```

### Kubernetes Deployment

**1. Create ConfigMap:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: chatbot-config
data:
  APP_NAME: "OpenAI Chatbot API"
  LOG_LEVEL: "INFO"
```

**2. Create Secret:**

```bash
kubectl create secret generic chatbot-secrets \
  --from-literal=database-url="postgresql+asyncpg://..." \
  --from-literal=openai-api-key="sk-..."
```

**3. Deploy Application:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chatbot-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: chatbot-api
  template:
    metadata:
      labels:
        app: chatbot-api
    spec:
      containers:
      - name: api
        image: openai-chatbot-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: chatbot-secrets
              key: database-url
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: chatbot-secrets
              key: openai-api-key
        envFrom:
        - configMapRef:
            name: chatbot-config
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
```

### Cloud Deployment

#### AWS (Elastic Beanstalk)

```bash
# Install EB CLI
pip install awsebcli

# Initialize EB application
eb init -p python-3.11 chatbot-api

# Create environment
eb create chatbot-api-env

# Deploy
eb deploy
```

#### Azure (App Service)

```bash
# Install Azure CLI
az login

# Create resource group
az group create --name chatbot-rg --location eastus

# Create App Service plan
az appservice plan create --name chatbot-plan --resource-group chatbot-rg --sku B1 --is-linux

# Create web app
az webapp create --resource-group chatbot-rg --plan chatbot-plan --name chatbot-api --runtime "PYTHON:3.11"

# Deploy
az webapp up --name chatbot-api
```

#### Google Cloud (Cloud Run)

```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT_ID/chatbot-api

# Deploy to Cloud Run
gcloud run deploy chatbot-api \
  --image gcr.io/PROJECT_ID/chatbot-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## Project Structure

```
postgresdb-8/
├── alembic/                      # Database migrations
│   ├── versions/                 # Migration files
│   └── env.py                    # Alembic configuration
├── src/
│   └── postgresdb_8/
│       ├── api/                  # API layer
│       │   ├── dependencies.py   # Dependency injection
│       │   └── routes/           # API endpoints
│       │       ├── chat.py       # Chat endpoints
│       │       └── health.py     # Health check endpoints
│       ├── config/               # Configuration
│       │   ├── __init__.py       # Config exports
│       │   ├── database.py       # Database config
│       │   └── settings.py       # Application settings
│       ├── middleware/           # Middleware
│       │   ├── error_handler.py  # Global error handler
│       │   └── request_id.py     # Request ID tracking
│       ├── models/               # Database models
│       │   ├── base.py           # Base model
│       │   ├── message.py        # Message model
│       │   └── thread.py         # Thread model
│       ├── schemas/              # Pydantic schemas
│       │   └── chat.py           # Chat request/response models
│       ├── services/             # Business logic
│       │   ├── chat_service.py   # Chat orchestration
│       │   ├── database_service.py # Database operations
│       │   └── openai_service.py # OpenAI integration
│       ├── utils/                # Utilities
│       │   ├── errors.py         # Custom exceptions
│       │   └── logging.py        # Logging configuration
│       ├── __init__.py
│       └── main.py               # Application entry point
├── tests/                        # Test suite
│   ├── test_chat_service.py
│   ├── test_database_service.py
│   └── test_openai_service.py
├── .env.example                  # Environment template
├── .gitignore
├── alembic.ini                   # Alembic configuration
├── pyproject.toml                # Project metadata
├── README.md                     # This file
└── requirements.txt              # Python dependencies
```

## Key Components

### Services Layer

- **`ChatService`** - Orchestrates chat operations, combines OpenAI and database services
- **`OpenAIService`** - Manages OpenAI API interactions (assistant, threads, messages)
- **`DatabaseService`** - Handles all database CRUD operations

### Middleware

- **`ErrorHandlerMiddleware`** - Global error handler with consistent JSON responses
- **`RequestIDMiddleware`** - Tracks requests with unique IDs for debugging

### Models

- **`ConversationThread`** - Stores thread metadata and token counts
- **`Message`** - Stores individual messages with role, content, and token usage

### Error Handling

Custom exception hierarchy:
- `ChatbotAPIError` - Base exception
- `ThreadNotFoundError` - Thread not found (404)
- `OpenAIServiceError` - OpenAI API errors (502)
- `DatabaseError` - Database errors (500)
- `ValidationError` - Request validation (422)

## Monitoring and Observability

### Structured Logging

All logs are JSON-formatted with:
- **timestamp** - ISO 8601 timestamp
- **level** - Log level (INFO, WARNING, ERROR)
- **message** - Log message
- **request_id** - Request tracking ID
- **extra_fields** - Context-specific data

**Example log entry:**
```json
{
  "timestamp": "2025-11-07T12:00:00.000Z",
  "level": "INFO",
  "name": "src.postgresdb_8.api.routes.chat",
  "message": "Chat message processed successfully",
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "extra_fields": {
    "thread_id": "thread_abc123",
    "total_tokens": 75,
    "prompt_tokens": 25,
    "completion_tokens": 50
  }
}
```

### Metrics

Token usage is tracked at multiple levels:
- **Per message** - Individual token counts
- **Per thread** - Cumulative token usage
- **Logged** - JSON logs include token metrics

### Health Checks

- **`/health`** - Full health check (API, database, OpenAI)
- **`/health/live`** - Liveness probe (is app running?)
- **`/health/ready`** - Readiness probe (can accept traffic?)

## Performance Optimization

### Database

- **Indexes** - All foreign keys and frequently queried columns
- **Connection pooling** - SQLAlchemy async engine with pool
- **Query optimization** - Efficient joins and pagination

### Caching

Consider implementing caching for:
- OpenAI assistant metadata
- Frequently accessed threads
- Token usage statistics

### Async Operations

- Fully async database operations
- Non-blocking OpenAI API calls
- Async middleware and dependencies

## Security Best Practices

1. **Environment Variables** - Never commit `.env` file
2. **API Keys** - Store securely, rotate regularly
3. **Database** - Use strong passwords, connection encryption
4. **CORS** - Configure allowed origins appropriately
5. **Rate Limiting** - Implement rate limiting for production
6. **Input Validation** - Pydantic models validate all inputs
7. **Error Messages** - Don't expose sensitive information

## Troubleshooting

### Common Issues

**1. Database Connection Error**
```
sqlalchemy.exc.OperationalError: could not connect to server
```
**Solution:** Check DATABASE_URL, ensure PostgreSQL is running

**2. OpenAI API Error**
```
OpenAIServiceError: Invalid API key
```
**Solution:** Verify OPENAI_API_KEY in `.env` file

**3. Migration Error**
```
alembic.util.exc.CommandError: Can't locate revision
```
**Solution:** Run `alembic upgrade head`

**4. Module Import Error**
```
ModuleNotFoundError: No module named 'postgresdb_8'
```
**Solution:** Ensure virtual environment is activated, dependencies installed

### Debug Mode

Enable detailed logging:
```bash
# Set in .env
LOG_LEVEL="DEBUG"
```

### Check Application Status

```bash
# Test database connection
python -c "from src.postgresdb_8.config.database import test_connection; import asyncio; asyncio.run(test_connection())"

# Verify OpenAI connection
python -c "from src.postgresdb_8.services.openai_service import OpenAIService; import asyncio; s = OpenAIService(); asyncio.run(s.initialize())"
```

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Add type hints to all functions
- Write tests for new features
- Update documentation
- Use conventional commit messages

### Code Quality

```bash
# Format code
black src/

# Lint code
ruff check src/

# Type checking
mypy src/
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [OpenAI](https://openai.com/) - AI capabilities
- [SQLAlchemy](https://www.sqlalchemy.org/) - Database ORM
- [Pydantic](https://docs.pydantic.dev/) - Data validation

## Support

For issues and questions:
- **GitHub Issues**: [Create an issue](https://github.com/mani5100/OpenAI-SDK/issues)
- **Documentation**: [API Docs](http://localhost:8000/docs)
- **Email**: m.abdulrehman.shoukat@gmail.com

## Changelog

### Version 1.0.0 (2025-11-07)

- ✅ Initial release
- ✅ OpenAI Agents SDK integration
- ✅ PostgreSQL persistence
- ✅ Streaming support via SSE
- ✅ Comprehensive error handling
- ✅ Structured logging
- ✅ Health monitoring
- ✅ API documentation
- ✅ Token usage tracking

---

**Built with ❤️ using FastAPI and OpenAI**
