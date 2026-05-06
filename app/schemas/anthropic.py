"""Anthropic API models."""
from typing import Literal, Optional, Any, Union
from pydantic import BaseModel, field_validator


class AnthropicMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: Union[str, list[dict[str, Any]]]

    @field_validator("content", mode="before")
    @classmethod
    def normalize_content(cls, v):
        """Allow content to be a string or list of dicts; convert plain string to list."""
        if isinstance(v, str):
            return [{"type": "text", "text": v}]
        return v


class AnthropicTool(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]


class AnthropicSystemContent(BaseModel):
    type: Literal["text"] = "text"
    text: str
    cache_control: Optional[dict[str, Any]] = None


class AnthropicRequest(BaseModel):
    model: str
    max_tokens: int = 4096
    messages: list[AnthropicMessage]
    system: Optional[Union[str, list[AnthropicSystemContent]]] = None
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