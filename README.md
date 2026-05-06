# xopenai

A production-ready HTTP proxy for translating Anthropic API requests to OpenAI format.

## Features

- Non-streaming and streaming responses
- Tool calling
- Retry logic with exponential backoff
- Prometheus metrics
- Rate limiting
- Structured logging with daily rotation
- Request size limits
- Optional authentication

## Quick Start

```bash
# Copy example configuration
cp conf/settings.json.example conf/settings.json

# Edit settings.json to add your API key
# Or use environment variable
export OPENAI__API_KEY=your-key

uvicorn app.main:app --reload
```

## API

- `POST /v1/messages` - Send messages
- `GET /v1/models` - List models
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics

## Configuration

The proxy uses `conf/settings.json` for configuration. For your first setup:

```bash
cp conf/settings.json.example conf/settings.json
```

Then edit `conf/settings.json` to configure:

- **OpenAI API**: Default endpoint is Qwen OpenAI-compatible API (`https://coding.dashscope.aliyuncs.com/v1`)
- **Model Mapping**: Maps Anthropic model names to backend models (default: `claude-3-5-sonnet-20241022` → `qwen3.6-plus`)
- **Security**: Optional API key authentication
- **Proxy Settings**: Retry, timeout, rate limiting

Environment variables override settings:
```bash
OPENAI__API_KEY=sk-dashscope-your-key
OPENAI__API_ENDPOINT=https://coding.dashscope.aliyuncs.com/v1
```

See `.env.example` for all available environment variables.

## Logging

Logs are stored in the `logs/` directory with structured JSON format. Log files rotate daily at midnight with a 7-day retention period. Log format:

```
[YYYY-MM-DD HH:MM:SS] [LEVEL] [module:line] message | {"extra": "fields"}
```

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