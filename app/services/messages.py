"""Service for /v1/messages."""
import time
import uuid
from typing import AsyncGenerator

from fastapi import HTTPException
from app.config import Settings
from app.schemas.anthropic import AnthropicRequest, AnthropicResponse
from app.converters.request import RequestConverter
from app.converters.response import ResponseConverter
from app.services.http_client import OpenAIClient
from app.logger import get_logger
from app.metrics import get_metrics

logger = get_logger(__name__)


class AnthropicMessagesService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = OpenAIClient(settings)
        self.request_converter = RequestConverter(settings.model_mapping)
        self.response_converter = ResponseConverter(
            {v: k for k, v in settings.model_mapping.items()}
        )
        self.metrics = get_metrics()

    async def handle_messages(self, request: AnthropicRequest) -> AnthropicResponse:
        request_id = str(uuid.uuid4())
        start_time = time.time()
        try:
            openai_request = self.request_converter.anthropic_to_openai(request)
            httpx_response = await self.client.send_request(
                "POST", "/chat/completions", json=openai_request.model_dump()
            )
            from app.schemas.openai import OpenAIResponse
            openai_response = OpenAIResponse(**httpx_response.json())
            anthropic_response = self.response_converter.openai_to_anthropic(
                openai_response, request.model
            )
            duration = time.time() - start_time
            self.metrics.requests_total.labels(method="POST", endpoint="/v1/messages", status="200").inc()
            self.metrics.request_duration.labels(method="POST", endpoint="/v1/messages").observe(duration)
            return anthropic_response
        except Exception as e:
            logger.error(f"Request failed: {e}", extra={"request_id": request_id})
            self.metrics.requests_total.labels(method="POST", endpoint="/v1/messages", status="500").inc()
            raise HTTPException(status_code=500, detail=str(e))

    async def handle_messages_stream(self, request: AnthropicRequest) -> AsyncGenerator[str, None]:
        request_id = str(uuid.uuid4())
        try:
            openai_request = self.request_converter.anthropic_to_openai(request)
            httpx_response = await self.client.send_request(
                "POST", "/chat/completions", json=openai_request.model_dump(), stream=True
            )
            async for line in httpx_response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    chunk = __import__('json').loads(data)
                    for event in self.response_converter.convert_stream_chunk(chunk):
                        yield f"event: {event.event}\ndata: {__import__('json').dumps(event.data)}\n\n"
        except Exception as e:
            logger.error(f"Stream failed: {e}", extra={"request_id": request_id})
            yield f'event: error\ndata: {{"type": "error", "message": "{str(e)}"}}\n\n'

    async def close(self) -> None:
        await self.client.close()