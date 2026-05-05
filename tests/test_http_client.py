"""Tests for HTTP client."""
import pytest
import respx
import httpx
from app.services.http_client import OpenAIClient
from app.config import Settings


@pytest.mark.asyncio
async def test_send_request():
    settings = Settings()
    client = OpenAIClient(settings)

    with respx.mock:
        respx.post("https://api.openai.com/v1/chat/completions").mock(
            return_value=httpx.Response(200, json={"id": "test", "choices": []})
        )
        response = await client.send_request("POST", "/chat/completions", json={"model": "gpt-4o"})
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_send_request_with_retry():
    from app.config import Settings
    from app.services.http_client import OpenAIClient

    settings = Settings.load_from_json("conf/settings.json")
    client = OpenAIClient(settings)

    attempt_count = 0

    async def mock_response(request):
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 2:
            return httpx.Response(500, json={"error": "server error"})
        return httpx.Response(200, json={"id": "test", "choices": []})

    with respx.mock:
        respx.post("https://coding.dashscope.aliyuncs.com/v1/chat/completions").mock(side_effect=mock_response)
        response = await client.send_request("POST", "/chat/completions", json={"model": "qwen-plus"})
        assert response.status_code == 200
        assert attempt_count >= 2