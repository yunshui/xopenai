"""Tests for Prometheus metrics."""
from app.metrics import Metrics, get_metrics


def test_metrics_singleton():
    """Test that get_metrics returns the same instance (singleton pattern)."""
    m1 = get_metrics()
    m2 = get_metrics()
    assert m1 is m2


def test_record_request():
    """Test that recording a request increments the counter."""
    metrics = get_metrics()
    before = metrics.requests_total.labels(method="POST", endpoint="/v1/messages", status="200")._value.get()
    metrics.record_request("POST", "/v1/messages", 200)
    after = metrics.requests_total.labels(method="POST", endpoint="/v1/messages", status="200")._value.get()
    assert after >= before + 1