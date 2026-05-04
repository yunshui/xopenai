"""Tests for services."""
import pytest
import httpx
from app.services.messages import AnthropicMessagesService
from app.services.models import AnthropicModelsService
from app.schemas.anthropic import AnthropicRequest, AnthropicMessage
from app.config import Settings


@pytest.mark.asyncio
async def test_handle_messages():
    settings = Settings()
    service = AnthropicMessagesService(settings)
    request = AnthropicRequest(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[AnthropicMessage(role="user", content=[{"type": "text", "text": "Hi"}])]
    )
    import respx
    with respx.mock:
        respx.post("https://api.openai.com/v1/chat/completions").mock(
            return_value=httpx.Response(200, json={
                "id": "chat-123",
                "object": "chat.completion",
                "created": 1234567890,
                "model": "gpt-4o",
                "choices": [{"index": 0, "message": {"role": "assistant", "content": "Hello!"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
            })
        )
        response = await service.handle_messages(request)
        assert response.id == "chat-123"
    await service.close()


@pytest.mark.asyncio
async def test_handle_messages_stream():
    from app.config import Settings
    from app.services.messages import AnthropicMessagesService

    settings = Settings.load_from_json("conf/settings.json")
    service = AnthropicMessagesService(settings)
    request = AnthropicRequest(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[AnthropicMessage(role="user", content=[{"type": "text", "text": "Hi"}])],
        stream=True
    )

    async def mock_stream_response(request):
        return httpx.Response(
            200,
            content=b'data: {"id":"chunk1","object":"chat.completion.chunk","created":1234567890,"model":"gpt-4o","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}\n\n',
            headers={"content-type": "text/event-stream"}
        )

    import respx
    with respx.mock:
        respx.post("https://api.openai.com/v1/chat/completions").mock(side_effect=mock_stream_response)
        events = []
        async for event in service.handle_messages_stream(request):
            events.append(event)
        assert len(events) > 0
    await service.close()


@pytest.mark.asyncio
async def test_list_models():
    settings = Settings()
    service = AnthropicModelsService(settings)
    import respx
    with respx.mock:
        respx.get("https://api.openai.com/v1/models").mock(
            return_value=httpx.Response(200, json={
                "object": "list",
                "data": [{"id": "gpt-4o"}, {"id": "gpt-4o-mini"}]
            })
        )
        response = await service.handle_models()
        assert response.object == "list"
        assert len(response.data) == 2
    await service.close()