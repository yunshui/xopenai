"""Prometheus metrics."""
from prometheus_client import Counter, Histogram, Gauge

from app.logger import get_logger

logger = get_logger(__name__)


class Metrics:
    """Prometheus metrics collector."""

    def __init__(self) -> None:
        """Initialize Prometheus metrics."""
        self.requests_total = Counter(
            "anthropic2openai_requests_total", "Total requests", ["method", "endpoint", "status"]
        )
        self.request_duration = Histogram(
            "anthropic2openai_request_duration_seconds", "Request duration", ["method", "endpoint"]
        )
        self.conversion_errors = Counter(
            "anthropic2openai_conversion_errors_total", "Conversion errors", ["converter", "error_type"]
        )
        self.retries_total = Counter("anthropic2openai_retries_total", "Retries", ["endpoint"])
        self.active_connections = Gauge("anthropic2openai_active_connections", "Active connections")

    def record_request(self, method: str, endpoint: str, status: int) -> None:
        """Record a request with method, endpoint, and status code."""
        self.requests_total.labels(method=method, endpoint=endpoint, status=status).inc()

    def record_request_duration(self, method: str, endpoint: str, duration: float) -> None:
        """Record a request duration in seconds."""
        self.request_duration.labels(method=method, endpoint=endpoint).observe(duration)


_metrics: Metrics | None = None


def get_metrics() -> Metrics:
    """Get the singleton Metrics instance."""
    global _metrics
    if _metrics is None:
        _metrics = Metrics()
    return _metrics