"""Convert Anthropic requests to OpenAI format."""
from typing import Any

from app.schemas.anthropic import AnthropicRequest, AnthropicMessage, AnthropicTool
from app.schemas.openai import OpenAIRequest, OpenAIMessage, OpenAITool, OpenAIFunction
from app.logger import get_logger

logger = get_logger(__name__)


class RequestConverter:
    def __init__(self, model_mapping: dict[str, str]) -> None:
        self.model_mapping = model_mapping

    def anthropic_to_openai(self, request: AnthropicRequest) -> OpenAIRequest:
        openai_model = self.model_mapping.get(request.model, request.model)
        messages: list[OpenAIMessage] = []
        if request.system:
            system_text = self._extract_system_text(request.system)
            messages.append(OpenAIMessage(role="system", content=system_text))
        for msg in request.messages:
            messages.extend(self._convert_message(msg))
        tools = [self._convert_tool(t) for t in request.tools] if request.tools else None
        return OpenAIRequest(
            model=openai_model,
            messages=messages,
            max_tokens=request.max_tokens,
            tools=tools,
            stream=request.stream,
            temperature=request.temperature,
            top_p=request.top_p,
        )

    def _extract_system_text(self, system) -> str:
        if isinstance(system, str):
            return system
        return "\n".join(block.text for block in system)

    def _convert_message(self, msg: AnthropicMessage) -> list[OpenAIMessage]:
        if msg.role == "user":
            content = "".join(b.get("text", "") for b in msg.content if b.get("type") == "text")
            return [OpenAIMessage(role="user", content=content)]
        elif msg.role == "assistant":
            result: list[OpenAIMessage] = []
            for block in msg.content:
                if block.get("type") == "text":
                    result.append(OpenAIMessage(role="assistant", content=block.get("text", "")))
            return result
        return []

    def _convert_tool(self, tool: AnthropicTool | dict[str, Any]) -> OpenAITool:
        if isinstance(tool, dict):
            return OpenAITool(
                type="function",
                function=OpenAIFunction(
                    name=tool["name"],
                    description=tool["description"],
                    parameters=tool["input_schema"],
                ),
            )
        return OpenAITool(
            type="function",
            function=OpenAIFunction(
                name=tool.name,
                description=tool.description,
                parameters=tool.input_schema,
            ),
        )