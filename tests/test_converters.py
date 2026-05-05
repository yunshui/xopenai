"""Tests for request/response converters."""
import pytest
from app.schemas.anthropic import AnthropicRequest, AnthropicMessage
from app.schemas.openai import OpenAIRequest, OpenAIResponse, OpenAIChoice, OpenAIUsage
from app.converters.request import RequestConverter
from app.converters.response import ResponseConverter


def test_convert_simple_message():
    anthropic = AnthropicRequest(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[AnthropicMessage(role="user", content=[{"type": "text", "text": "Hello"}])]
    )
    converter = RequestConverter({"claude-3-5-sonnet-20241022": "gpt-4o"})
    openai = converter.anthropic_to_openai(anthropic)
    assert isinstance(openai, OpenAIRequest)
    assert openai.model == "gpt-4o"


def test_convert_with_tools():
    anthropic = AnthropicRequest(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[AnthropicMessage(role="user", content=[{"type": "text", "text": "Hi"}])],
        tools=[{
            "name": "get_weather",
            "description": "Get weather",
            "input_schema": {"type": "object"}
        }]
    )
    converter = RequestConverter({"claude-3-5-sonnet-20241022": "gpt-4o"})
    openai = converter.anthropic_to_openai(anthropic)
    assert openai.tools is not None
    assert len(openai.tools) == 1
    assert openai.tools[0].type == "function"
    assert openai.tools[0].function.name == "get_weather"


def test_convert_response():
    openai = OpenAIResponse(
        id="resp_123",
        created=1234567890,
        model="gpt-4o",
        choices=[OpenAIChoice(
            index=0,
            message={"role": "assistant", "content": "Hello!"},
            finish_reason="stop"
        )],
        usage=OpenAIUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
    )
    converter = ResponseConverter({"gpt-4o": "claude-3-5-sonnet-20241022"})
    anthropic = converter.openai_to_anthropic(openai, "claude-3-5-sonnet-20241022")
    assert anthropic.id == "resp_123"
    assert anthropic.model == "claude-3-5-sonnet-20241022"
    assert anthropic.content[0]["text"] == "Hello!"


def test_convert_stream_chunk():
    converter = ResponseConverter({"gpt-4o": "claude-3-5-sonnet-20241022"})
    chunk = {
        "id": "test",
        "object": "chat.completion.chunk",
        "created": 1234567890,
        "model": "gpt-4o",
        "choices": [{"index": 0, "delta": {"content": "Hello"}, "finish_reason": None}]
    }
    events = list(converter.convert_stream_chunk(chunk))
    assert len(events) > 0
    assert any(e.event == "content_block_delta" for e in events)


def test_is_retryable_error_none():
    from app.converters.retry import is_retryable_error
    assert is_retryable_error(None) is True


def test_is_retryable_error_500():
    from app.converters.retry import is_retryable_error
    assert is_retryable_error(500) is True


def test_is_retryable_error_429():
    from app.converters.retry import is_retryable_error
    assert is_retryable_error(429) is True


def test_is_retryable_error_400():
    from app.converters.retry import is_retryable_error
    assert is_retryable_error(400) is False


@pytest.mark.asyncio
async def test_retry_manager_success():
    from app.converters.retry import RetryManager
    import httpx

    async def mock_request():
        return httpx.Response(200, json={"status": "ok"})

    manager = RetryManager(max_retries=2, delay=0.01)
    response = await manager.execute_with_retry("test_endpoint", mock_request)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_retry_manager_with_retry():
    from app.converters.retry import RetryManager
    import httpx

    manager = RetryManager(max_retries=2, delay=0.01)

    async def failing_request():
        raise httpx.HTTPStatusError(
            "Server error",
            request=httpx.Request("POST", "https://test.com"),
            response=httpx.Response(500),
        )

    with pytest.raises(httpx.HTTPStatusError):
        await manager.execute_with_retry("test_endpoint", failing_request)