"""Tests for authentication."""
import pytest
import httpx
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_auth_disabled():
    import respx
    with respx.mock:
        respx.post("https://api.openai.com/v1/chat/completions").mock(
            return_value=httpx.Response(200, json={
                "id": "test",
                "object": "chat.completion",
                "created": 1234567890,
                "model": "gpt-4o",
                "choices": [{"index": 0, "message": {"role": "assistant", "content": "Hi"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8}
            })
        )
        resp = client.post("/v1/messages", json={
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 100,
            "messages": [{"role": "user", "content": [{"type": "text", "text": "Hi"}]}]
        }, headers={"x-api-key": "invalid"})
        # Should not 401 since auth is disabled by default
        assert resp.status_code != 401