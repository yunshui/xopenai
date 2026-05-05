"""Tests for routes."""
from fastapi.testclient import TestClient
import httpx
from app.main import app

client = TestClient(app)

def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"

def test_metrics():
    resp = client.get("/metrics")
    assert resp.status_code == 200


def test_messages_endpoint():
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
        })
        assert resp.status_code == 200
        assert resp.json()["id"] == "test"


def test_models_endpoint():
    import respx
    with respx.mock:
        respx.get("https://api.openai.com/v1/models").mock(
            return_value=httpx.Response(200, json={
                "object": "list",
                "data": [{"id": "gpt-4o"}, {"id": "gpt-4o-mini"}]
            })
        )
        resp = client.get("/v1/models")
        assert resp.status_code == 200
        assert resp.json()["object"] == "list"
        assert len(resp.json()["data"]) == 2


def test_messages_streaming():
    import respx
    def stream_gen():
        yield b'data: {"id":"chat-123","object":"chat.completion.chunk","created":1234567890,"model":"gpt-4o","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}\n\n'
        yield b'data: {"id":"chat-123","object":"chat.completion.chunk","created":1234567890,"model":"gpt-4o","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}\n\n'
        yield b'data: [DONE]\n\n'

    with respx.mock:
        respx.post("https://api.openai.com/v1/chat/completions").mock(
            return_value=httpx.Response(200, stream=stream_gen())
        )
        resp = client.post("/v1/messages", json={
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 100,
            "messages": [{"role": "user", "content": [{"type": "text", "text": "Hi"}]}],
            "stream": True
        })
        assert resp.status_code == 200
        assert b"event:" in resp.content


def test_request_too_large():
    large = "x" * (11 * 1024 * 1024)
    resp = client.post("/v1/messages", json={
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 100,
        "messages": [{"role": "user", "content": [{"type": "text", "text": large}]}]
    })
    assert resp.status_code == 413