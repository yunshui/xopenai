"""Anthropic API models."""
from typing import Literal, Optional, Any
from pydantic import BaseModel


class AnthropicMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: list[dict[str, Any]]


class AnthropicTool(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]


class AnthropicRequest(BaseModel):
    model: str
    max_tokens: int
    messages: list[AnthropicMessage]
    system: Optional[str] = None
    tools: Optional[list[AnthropicTool]] = None
    stream: bool = False
    temperature: Optional[float] = None
    top_p: Optional[float] = None


class AnthropicUsage(BaseModel):
    input_tokens: int
    output_tokens: int


class AnthropicResponse(BaseModel):
    id: str
    type: Literal["message"] = "message"
    role: Literal["assistant"] = "assistant"
    content: list[dict[str, Any]]
    model: str
    stop_reason: Optional[str] = None
    usage: AnthropicUsage


class AnthropicModelsResponse(BaseModel):
    object: Literal["list"] = "list"
    data: list[dict[str, str]]