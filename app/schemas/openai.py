"""OpenAI API models."""
from typing import Literal, Optional, Any, List
from pydantic import BaseModel


class OpenAIMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str | List[dict[str, Any]]
    tool_call_id: Optional[str] = None


class OpenAIFunction(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]


class OpenAITool(BaseModel):
    type: Literal["function"] = "function"
    function: OpenAIFunction


class OpenAIRequest(BaseModel):
    model: str
    messages: list[OpenAIMessage]
    max_tokens: int
    tools: Optional[list[OpenAITool]] = None
    stream: bool = False
    temperature: Optional[float] = None
    top_p: Optional[float] = None


class OpenAIUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class OpenAIChoice(BaseModel):
    index: int
    message: dict[str, Any]
    finish_reason: Optional[str] = None


class OpenAIResponse(BaseModel):
    id: str
    object: Literal["chat.completion"] = "chat.completion"
    created: int
    model: str
    choices: list[OpenAIChoice]
    usage: OpenAIUsage


class OpenAIModelsResponse(BaseModel):
    object: Literal["list"] = "list"
    data: list[dict[str, str]]