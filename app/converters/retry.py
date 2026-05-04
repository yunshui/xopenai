"""Retry logic."""
import asyncio
from typing import Callable, Awaitable
import httpx
from app.metrics import get_metrics
from app.logger import get_logger

logger = get_logger(__name__)


def is_retryable_error(status_code: int | None) -> bool:
    if status_code is None:
        return True
    return status_code >= 500 or status_code == 429


class RetryManager:
    def __init__(self, max_retries: int = 3, delay: float = 1.0, backoff_multiplier: float = 2.0) -> None:
        self.max_retries = max_retries
        self.delay = delay
        self.backoff_multiplier = backoff_multiplier
        self.metrics = get_metrics()

    async def execute_with_retry(
        self, endpoint: str, request_func: Callable[[], Awaitable[httpx.Response]]
    ) -> httpx.Response:
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                return await request_func()
            except (httpx.TimeoutException, httpx.RequestError) as e:
                last_error = e
                logger.warning(f"Request failed (attempt {attempt + 1})", extra={"endpoint": endpoint})
            except httpx.HTTPStatusError as e:
                if is_retryable_error(e.response.status_code):
                    last_error = e
                    logger.warning(f"Retryable error {e.response.status_code}")
                else:
                    raise
            if attempt < self.max_retries:
                self.metrics.retries_total.labels(endpoint=endpoint).inc()
                await asyncio.sleep(self.delay * (self.backoff_multiplier ** attempt))
        raise last_error or RuntimeError("Request failed")