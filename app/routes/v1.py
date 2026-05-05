"""v1 API routes."""
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from slowapi import Limiter

from app.config import Settings
from app.schemas.anthropic import AnthropicRequest, AnthropicModelsResponse
from app.services.messages import AnthropicMessagesService
from app.services.models import AnthropicModelsService
from app.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/v1", tags=["v1"])

# Limiter will be set from main.py
_limiter: Limiter | None = None

# Services will be set from main.py
_messages_service: AnthropicMessagesService | None = None
_models_service: AnthropicModelsService | None = None
_settings: Settings | None = None


def set_limiter(limiter: Limiter) -> None:
    global _limiter
    _limiter = limiter


def set_services(messages: AnthropicMessagesService, models: AnthropicModelsService, settings: Settings) -> None:
    global _messages_service, _models_service, _settings
    _messages_service = messages
    _models_service = models
    _settings = settings


@router.post("/messages")
async def create_message(request: AnthropicRequest, http_request: Request):
    service = _messages_service
    if request.stream:
        return StreamingResponse(
            service.handle_messages_stream(request),
            media_type="text/event-stream",
        )
    return await service.handle_messages(request)


@router.get("/models", response_model=AnthropicModelsResponse)
async def list_models():
    service = _models_service
    return await service.handle_models()