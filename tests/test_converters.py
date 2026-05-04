"""Tests for request/response converters."""
import pytest
from app.schemas.anthropic import AnthropicRequest, AnthropicMessage, AnthropicTool
from app.schemas.openai import OpenAIRequest
from app.converters.request import RequestConverter


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