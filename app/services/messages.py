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

    async def handle_messages(self, request: AnthropicRequest, request_id: str | None = None) -> AnthropicResponse:
        if request_id is None:
            request_id = str(uuid.uuid4())
        start_time = time.time()
        try:
            # Log original Anthropic request
            logger.debug(f"Original Anthropic request: {request.model_dump_json()}", extra={"request_id": request_id, "step": "1_original_request"})

            # Convert to OpenAI format
            openai_request = self.request_converter.anthropic_to_openai(request)
            logger.debug(f"Converted OpenAI request: {openai_request.model_dump_json()}", extra={"request_id": request_id, "step": "2_openai_request"})

            # Send to OpenAI service
            httpx_response = await self.client.send_request(
                "POST", "/chat/completions", json=openai_request.model_dump(exclude_none=True)
            )
            from app.schemas.openai import OpenAIResponse
            openai_response = OpenAIResponse(**httpx_response.json())
            logger.debug(f"OpenAI service response: {httpx_response.text}", extra={"request_id": request_id, "step": "3_openai_response"})

            # Convert back to Anthropic format
            anthropic_response = self.response_converter.openai_to_anthropic(
                openai_response, request.model
            )
            logger.debug(f"Converted Anthropic response: {anthropic_response.model_dump_json()}", extra={"request_id": request_id, "step": "4_anthropic_response"})

            duration = time.time() - start_time
            self.metrics.requests_total.labels(method="POST", endpoint="/v1/messages", status="200").inc()
            self.metrics.request_duration.labels(method="POST", endpoint="/v1/messages").observe(duration)
            return anthropic_response
        except Exception as e:
            logger.error(f"Request failed: {e}", extra={"request_id": request_id})
            self.metrics.requests_total.labels(method="POST", endpoint="/v1/messages", status="500").inc()
            raise HTTPException(status_code=500, detail=str(e))

    async def handle_messages_stream(self, request: AnthropicRequest, request_id: str | None = None) -> AsyncGenerator[str, None]:
        if request_id is None:
            request_id = str(uuid.uuid4())
        try:
            # Log original Anthropic request
            logger.debug(f"Original Anthropic request (stream): {request.model_dump_json()}", extra={"request_id": request_id, "step": "1_original_request"})

            # Convert to OpenAI format
            openai_request = self.request_converter.anthropic_to_openai(request)
            logger.debug(f"Converted OpenAI request (stream): {openai_request.model_dump_json()}", extra={"request_id": request_id, "step": "2_openai_request"})

            # Send to OpenAI service
            httpx_response = await self.client.send_request(
                "POST", "/chat/completions", json=openai_request.model_dump(exclude_none=True), stream=True
            )

            # Log stream start
            logger.debug(f"OpenAI stream started", extra={"request_id": request_id, "step": "3_stream_start"})

            chunk_count = 0
            async for line in httpx_response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    chunk = __import__('json').loads(data)
                    for event in self.response_converter.convert_stream_chunk(chunk):
                        yield f"event: {event.event}\ndata: {__import__('json').dumps(event.data)}\n\n"
                    chunk_count += 1

            # Log stream completion
            logger.debug(f"OpenAI stream completed, chunks: {chunk_count}", extra={"request_id": request_id, "step": "4_stream_complete"})
        except Exception as e:
            logger.error(f"Stream failed: {e}", extra={"request_id": request_id})
            yield f'event: error\ndata: {{"type": "error", "message": "{str(e)}"}}\n\n'

    async def close(self) -> None:
        await self.client.close()