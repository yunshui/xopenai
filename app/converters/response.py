"""Convert OpenAI responses to Anthropic format."""
from typing import Any, Generator

from app.schemas.openai import OpenAIResponse
from app.schemas.anthropic import AnthropicResponse, AnthropicUsage
from app.logger import get_logger

logger = get_logger(__name__)


class AnthropicStreamEvent:
    def __init__(self, event: str, data: dict[str, Any]) -> None:
        self.event = event
        self.data = data


class ResponseConverter:
    def __init__(self, model_mapping: dict[str, str]) -> None:
        self.model_mapping = model_mapping

    def openai_to_anthropic(self, response: OpenAIResponse, original_model: str) -> AnthropicResponse:
        choice = response.choices[0]
        message = choice.message
        content: list[dict[str, Any]] = []
        if isinstance(message.get("content"), str):
            content.append({"type": "text", "text": message["content"]})
        tool_calls = message.get("tool_calls")
        if tool_calls:
            for tc in tool_calls:
                content.append({
                    "type": "tool_use",
                    "id": tc["id"],
                    "name": tc["function"]["name"],
                    "input": __import__("json").loads(tc["function"]["arguments"]),
                })
        usage = AnthropicUsage(
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
        )
        stop_reason = self._map_stop_reason(choice.finish_reason)
        return AnthropicResponse(
            id=response.id,
            model=original_model,
            content=content,
            usage=usage,
            stop_reason=stop_reason,
        )

    def convert_stream_chunk(self, chunk: dict[str, Any]) -> Generator[AnthropicStreamEvent, None, None]:
        if not chunk.get("choices"):
            return
        choice = chunk["choices"][0]
        delta = choice.get("delta", {})
        if "content" in delta:
            yield AnthropicStreamEvent(
                event="content_block_delta",
                data={
                    "type": "content_block_delta",
                    "index": 0,
                    "delta": {"type": "text_delta", "text": delta["content"]},
                },
            )
        if delta.get("tool_calls"):
            for tc in delta["tool_calls"]:
                yield AnthropicStreamEvent(
                    event="content_block_delta",
                    data={
                        "type": "content_block_delta",
                        "index": tc.get("index", 0),
                        "delta": {
                            "type": "input_json_delta",
                            "partial_json": tc.get("function", {}).get("arguments", ""),
                        },
                    },
                )
        if choice.get("finish_reason"):
            yield AnthropicStreamEvent(
                event="message_delta",
                data={"type": "message_delta", "delta": {"stop_reason": choice["finish_reason"]}},
            )

    def _map_stop_reason(self, openai_reason: str | None) -> str | None:
        mapping = {"stop": "end_turn", "length": "max_tokens", "tool_calls": "tool_use"}
        return mapping.get(openai_reason) if openai_reason else None