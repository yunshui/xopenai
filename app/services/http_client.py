"""HTTP client for OpenAI API."""
import asyncio
from typing import Any
import httpx
from app.config import Settings
from app.converters.retry import RetryManager
from app.metrics import get_metrics
from app.logger import get_logger

logger = get_logger(__name__)


class OpenAIClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.endpoint = settings.openai_api_endpoint
        self.api_key = settings.openai_api_key
        self.timeout = settings.proxy_timeout
        self.semaphore = asyncio.Semaphore(settings.proxy_max_concurrent_requests)
        self.retry_manager = RetryManager(
            max_retries=settings.proxy_max_retries,
            delay=settings.proxy_retry_delay,
            backoff_multiplier=settings.proxy_retry_backoff_multiplier,
        )
        self.metrics = get_metrics()
        self._client: httpx.AsyncClient | None = None

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()

    async def send_request(
        self, method: str, path: str, json: dict[str, Any] | None = None, stream: bool = False
    ) -> httpx.Response:
        async with self.semaphore:
            self.metrics.active_connections.inc()
            try:
                client = await self.get_client()
                url = f"{self.endpoint}{path}"
                logger.info(f"Sending {method} {path}")
                async def _request() -> httpx.Response:
                    resp = await client.request(
                        method, url, json=json,
                        headers={"Authorization": f"Bearer {self.api_key}"}
                    )
                    resp.raise_for_status()
                    return resp
                if stream:
                    return await _request()
                return await self.retry_manager.execute_with_retry(path, _request)
            finally:
                self.metrics.active_connections.dec()