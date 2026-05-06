# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

xopenai is a production-ready HTTP proxy that translates Anthropic API requests to OpenAI-compatible format. It supports:
- Non-streaming and streaming responses
- Tool calling
- Model name mapping (e.g., `claude-3-5-sonnet-20241022` → `qwen3.6-plus`)
- Retry logic with exponential backoff
- Prometheus metrics
- Rate limiting
- Structured logging with daily rotation

## Common Development Commands

### Running the Application
```bash
# Local development with hot reload
uvicorn app.main:app --reload

# With custom port
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Configuration
```bash
# Copy example configuration and edit it
cp conf/settings.json.example conf/settings.json

# Or use environment variables (override settings.json)
export OPENAI__API_KEY=your-key
export OPENAI__API_ENDPOINT=https://coding.dashscope.aliyuncs.com/v1
export LOG_LEVEL=DEBUG
```

### Testing
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=app tests/

# Run a specific test file
pytest tests/test_routes.py

# Run specific test
pytest tests/test_routes.py -k test_create_message
```

### Linting and Code Quality
```bash
# Check code style and lint
ruff check app/ tests/

# Auto-fix issues
ruff check --fix app/ tests/

# Format code
ruff format app/ tests/
```

### Docker
```bash
# Build and run with docker-compose
docker-compose up --build

# Run just the proxy
docker build -t xopenai .
docker run -p 8000:8000 -e OPENAI__API_KEY=your-key xopenai
```

## Architecture Overview

The proxy follows a clean layered architecture:

```
FastAPI (app/main.py)
  ↓
Routes (app/routes/v1.py)
  ↓
Services (app/services/)
  ↓
Converters (app/converters/)
  ↓
HTTP Client (app/services/http_client.py) → OpenAI API
```

### Request Flow

1. **Main Application** (`app/main.py`): Initializes FastAPI, middleware (CORS, rate limiting, request ID tracking), and services
2. **Routes** (`app/routes/v1.py`): Handles `/v1/messages` (POST) and `/v1/models` (GET) endpoints
3. **Services**:
   - `AnthropicMessagesService`: Converts request → calls OpenAI → converts response
   - `AnthropicModelsService`: Returns model list
4. **Converters**:
   - `RequestConverter`: Anthropic format → OpenAI format (handles messages, tools, system prompts)
   - `ResponseConverter`: OpenAI format → Anthropic format (handles streaming/non-streaming)
5. **HTTP Client** (`app/services/http_client.py`): Manages requests with retry logic, concurrency limits, and connection pooling

### Configuration System

Configuration is managed through `app/config.py` using pydantic-settings:

- **Priority**: Environment variables → `conf/settings.json` → defaults
- **Naming**: Uses `__` as nested delimiter (e.g., `OPENAI__API_KEY`)
- **Model mapping**: Maps Anthropic model names to backend models via `model_mapping` dict

### Key Components

- **Retry Logic** (`app/converters/retry.py`): Exponential backoff for 5xx errors and 429 rate limits
- **Logging** (`app/logger.py`): Structured JSON logs with daily rotation, includes client IP and request ID
- **Metrics** (`app/metrics.py`): Prometheus metrics for requests, duration, errors, retries, and active connections
- **Schemas** (`app/schemas/`): Pydantic models for Anthropic and OpenAI API formats

### Streaming

Streaming responses use Server-Sent Events (SSE). The proxy converts OpenAI SSE chunks to Anthropic event format:
- `content_block_delta` for text deltas
- `message_delta` for stop_reason

### Request ID Tracking

Every request gets a unique UUID assigned in middleware. The request ID is:
- Logged with all messages
- Included in response headers (`X-Request-ID`)
- Used to correlate logs across the request lifecycle

### Security Features

- Optional API key authentication via `x-api-key` header
- CORS configurable via `security_allowed_origins`
- Request size limits via `proxy_max_request_size_mb`
- Security headers on all responses

## Documentation Index

This project maintains several documents that provide different perspectives on the codebase:

### User Documentation
- **README.md** (English) - Project overview, quick start guide, API endpoints, configuration reference
- **README.zh.md** (Chinese) - Same content as README.md but in Chinese

### Development Documentation
- **docs/progress.md** - Complete development progress tracking with:
  - 19-task implementation plan and completion status
  - Detailed commit history per task
  - Code review process and results
  - Final quality metrics (100% completion, 94% coverage)
  - Technical decisions and rationale
  - Lessons learned from design and implementation phases

### Architecture and Design Documentation
- **docs/superpowers/specs/2026-05-04-xopenai-design.md** - Approved design specification (Status: APPROVED, Version 1.1):
  - Component architecture diagrams
  - Request/response flow specifications
  - Configuration structure and environment variables
  - Retry logic and error handling strategies
  - Security and rate limiting details
  - Monitoring and metrics specification
  - Testing strategy and coverage goals
  - Technical stack decisions

- **docs/superpowers/plans/2026-05-04-xopenai.md** - Approved implementation plan with:
  - 19 detailed tasks with step-by-step instructions
  - Code examples for each component
  - Test specifications using TDD approach
  - File-by-file implementation guide

### Project Statistics (as of completion)
- **Total Tasks**: 19 (all completed)
- **Test Count**: 36 (100% passing)
- **Code Coverage**: 94%
- **Lines of Code**: 499
- **Start Date**: 2026-05-04
- **Completion Date**: 2026-05-04