# Anthropic to OpenAI API Proxy - Design Document

**Date:** 2026-05-04
**Status:** Approved
**Version:** 1.0

## Overview

A production-ready HTTP proxy that receives Anthropic API requests and forwards them to OpenAI API with appropriate format translation. The proxy supports non-streaming, streaming, and tool calling.

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Application                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │/v1/messages│ │/v1/models│ │/v1/... │ │/metrics│ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘ │
│       │             │             │            │      │
│  ┌────▼─────────────▼─────────────▼────────────▼────┐ │
│  │              Route Dispatcher                     │ │
│  └────────────────────┬─────────────────────────────┘ │
│                       │                                 │
│  ┌────────────────────▼─────────────────────────────┐ │
│  │         Conversion Layer                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │ │
│  │  │ Request     │  │ Response    │  │ Retry     │ │ │
│  │  │ Converter   │  │ Converter   │  │ Manager   │ │ │
│  │  └─────────────┘  └─────────────┘  └───────────┘ │ │
│  └────────────────────┬─────────────────────────────┘ │
│                       │                                 │
│  ┌────────────────────▼─────────────────────────────┐ │
│  │         HTTP Client Layer                        │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Core Components

1. **FastAPI Application Layer**
   - Route definitions: `/v1/messages`, `/v1/models`, `/health`, `/metrics`
   - Request validation and response serialization
   - CORS and middleware configuration

2. **Route Dispatcher**
   - Routes requests to appropriate handlers
   - Unified exception handling and error response format

3. **Conversion Layer**
   - `RequestConverter`: Converts Anthropic format to OpenAI format
   - `ResponseConverter`: Converts OpenAI format back to Anthropic format
   - Supported message types: regular messages, streaming messages, tool calls
   - `RetryManager`: Manages retry logic with exponential backoff

4. **HTTP Client Layer**
   - Async client based on `httpx`
   - Configurable timeout and concurrency limits
   - Connection pool management

5. **Infrastructure Layer**
   - `Logger`: Structured logging (class name, line number, parameters)
   - `Config`: Configuration management (env vars + settings.json)
   - `Metrics`: Prometheus metrics collection

6. **Service Layer**
   - `AnthropicMessagesService`: Handles `/v1/messages`
   - `AnthropicModelsService`: Handles `/v1/models`

## Data Flow

### Request Flow (/v1/messages)

```
Client Request
    ↓
FastAPI Route (validate request body)
    ↓
AnthropicMessagesService
    ↓
RequestConverter.anthropic_to_openai()
    ↓
HTTP Client (with retry, timeout)
    ↓
OpenAI API
    ↓
OpenAI Response
    ↓
ResponseConverter.openai_to_anthropic()
    ↓
FastAPI Response (streaming/non-streaming)
    ↓
Client
```

### Streaming Response Handling

- Streaming mode uses FastAPI's `StreamingResponse`
- Converter transforms SSE events chunk by chunk
- On client disconnect: continue receiving, log, don't send

### Tool Calling Flow

```
Anthropic tools format
    ↓
Convert to OpenAI function calling format
    ↓
OpenAI processing
    ↓
OpenAI function calling response
    ↓
Convert back to Anthropic tools format
```

## Configuration

### Configuration Structure (conf/settings.json)

```json
{
  "anthropic": {
    "api_endpoint": "http://localhost:8000/v1"
  },
  "openai": {
    "api_endpoint": "https://api.openai.com/v1",
    "api_key": "${OPENAI_API_KEY}"
  },
  "proxy": {
    "max_retries": 3,
    "timeout": 30,
    "retry_delay": 1,
    "max_concurrent_requests": 50
  },
  "logging": {
    "level": "INFO",
    "log_dir": "logs",
    "max_file_size": "10MB",
    "backup_count": 7
  }
}
```

### Environment Variables

Environment variables take precedence over settings.json:
- `OPENAI_API_KEY`: OpenAI API key
- `LOG_LEVEL`: Override logging level
- `MAX_RETRIES`: Override max retry count
- `TIMEOUT`: Override timeout in seconds

### Logging

**Log Format:**
```
[2026-05-04 10:30:45] [INFO] [AnthropicMessagesService:85] Request received - model: claude-3-5-sonnet-20241022, stream: true
[2026-05-04 10:30:46] [ERROR] [RetryManager:42] Request failed after 3 retries - reason: timeout, elapsed: 95s
```

**Features:**
- Daily rotation: `logs/anthropic2openai-2026-05-04.log`
- Includes: timestamp, level, class:line, message
- Structured logging: key parameters, error details as JSON
- Log levels: DEBUG, INFO, WARNING, ERROR (configurable)

## Project Structure

```
anthropic2openai/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry
│   ├── config.py            # Configuration management
│   ├── logger.py            # Logging utility
│   ├── metrics.py           # Prometheus metrics
│   ├── converters/          # Conversion layer
│   │   ├── __init__.py
│   │   ├── request.py       # Request conversion
│   │   ├── response.py      # Response conversion
│   │   └── retry.py         # Retry management
│   ├── services/            # Business service layer
│   │   ├── __init__.py
│   │   ├── messages.py      # /v1/messages
│   │   └── models.py        # /v1/models
│   ├── routes/              # Route definitions
│   │   ├── __init__.py
│   │   ├── v1.py            # v1 API routes
│   │   └── health.py        # Health check routes
│   └── schemas/             # Data models
│       ├── __init__.py
│       ├── anthropic.py     # Anthropic format
│       └── openai.py        # OpenAI format
├── conf/
│   └── settings.json        # Configuration file
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # pytest fixtures
│   ├── test_converters.py   # Converter tests
│   ├── test_services.py     # Service tests
│   └── test_routes.py       # Route tests
├── logs/                    # Log directory
├── docs/                    # Documentation
│   ├── design.md            # Design document
│   ├── development.md       # Development documentation
│   ├── testing.md           # Testing documentation
│   └── progress.md          # Progress tracking
├── .gitignore
├── pyproject.toml           # Project configuration
├── Dockerfile
├── docker-compose.yml
├── README.md                # English documentation
└── README.zh.md             # Chinese documentation
```

## API Endpoint Mapping

| Anthropic Endpoint | OpenAI Endpoint |
|--------------------|-----------------|
| POST /v1/messages  | POST /v1/chat/completions |
| GET /v1/models     | GET /v1/models |

## Error Handling

**Unified Error Response Format:**
```json
{
  "error": {
    "type": "api_error",
    "message": "Request failed: timeout",
    "request_id": "req_abc123",
    "details": {}
  }
}
```

- **Conversion failure**: 422 error, logged
- **API request failure**: Return OpenAI's original error (converted format)
- **Timeout/retry exhausted**: 504 error
- **Client disconnect**: Log, continue processing

## Monitoring

### Prometheus Metrics

```python
# Request count
anthropic2openai_requests_total{method, endpoint, status}

# Request duration
anthropic2openai_request_duration_seconds{method, endpoint}

# Conversion errors
anthropic2openai_conversion_errors_total{converter, error_type}

# Retry count
anthropic2openai_retries_total{endpoint}

# Active connections
anthropic2openai_active_connections
```

### Health Check Endpoints

- `GET /health`: Returns 200 + service status
- `GET /metrics`: Prometheus format metrics

## Testing Strategy

### Test Coverage Goals
- Conversion layer: 90%+
- Service layer: 85%+
- Overall: 80%+

### Test Types

1. **Unit Tests**
   - Request converters: various message formats, streaming, tool calls
   - Response converters: various response formats, streaming chunks
   - Retry manager: retry count, delay, timeout

2. **Integration Tests**
   - Service layer complete request-response flow
   - Mock OpenAI API using pytest-mock

3. **End-to-End Tests**
   - Start test server, send real requests
   - Verify logs and metrics

## Deployment

### Runtime
- ASGI server: uvicorn/gunicorn
- Containerization: Docker
- Minimum concurrency: 50 concurrent requests

## Technical Stack

- **Web Framework**: FastAPI
- **HTTP Client**: httpx (async)
- **Testing**: pytest, pytest-asyncio, pytest-mock
- **Metrics**: prometheus-client
- **Logging**: Python logging with rotation
- **Configuration**: pydantic-settings
- **Type Hints**: Python 3.10+