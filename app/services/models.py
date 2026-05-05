"""Service for /v1/models."""
from app.config import Settings
from app.schemas.anthropic import AnthropicModelsResponse
from app.services.http_client import OpenAIClient
from app.metrics import get_metrics


class AnthropicModelsService:
    def __init__(self, settings: Settings) -> None:
        self.client = OpenAIClient(settings)
        self.metrics = get_metrics()

    async def handle_models(self) -> AnthropicModelsResponse:
        httpx_response = await self.client.send_request("GET", "/models")
        openai_response = httpx_response.json()
        data = [{"id": m["id"], "display_name": m["id"]} for m in openai_response.get("data", [])]
        self.metrics.requests_total.labels(method="GET", endpoint="/v1/models", status="200").inc()
        return AnthropicModelsResponse(object="list", data=data)

    async def close(self) -> None:
        await self.client.close()