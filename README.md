# Anthropic to OpenAI API Proxy

A production-ready HTTP proxy for translating Anthropic API requests to OpenAI format.

## Features

- Non-streaming and streaming responses
- Tool calling
- Retry logic with exponential backoff
- Prometheus metrics
- Rate limiting
- Structured logging
- Request size limits
- Optional authentication

## Quick Start

```bash
export OPENAI_API_KEY=your-key
uvicorn app.main:app --reload
```

## API

- `POST /v1/messages` - Send messages
- `GET /v1/models` - List models
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics

## Configuration

See `conf/settings.json`. Environment variables override settings.

## Testing

```bash
pytest tests/
```

## Docker Deployment

```bash
docker-compose up
```

## License

MIT