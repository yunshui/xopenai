"""Tests for structured logging utility."""
import pytest
from app.logger import get_logger, setup_logging, StructuredFormatter
import logging


def test_get_logger():
    logger = get_logger("TestModule")
    assert logger.name == "TestModule"


def test_logger_format(tmp_path, caplog):
    setup_logging(log_dir=str(tmp_path))
    logger = get_logger("TestClass")
    with caplog.at_level("INFO"):
        logger.info("Test message")
    assert any("TestClass" in record.name for record in caplog.records)


def test_formatter_output():
    formatter = StructuredFormatter()
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="test.py",
        lineno=1, msg="test", args=(), exc_info=None
    )
    result = formatter.format(record)
    assert "[" in result  # timestamp
    assert "[INFO]" in result
    assert "test:1" in result


def test_extra_fields():
    formatter = StructuredFormatter()
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="test.py",
        lineno=1, msg="test", args=(), exc_info=None
    )
    record.user_id = "123"
    result = formatter.format(record)
    assert "user_id" in result
    assert '"123"' in result


def test_extra_fields_no_system_attrs():
    formatter = StructuredFormatter()
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="test.py",
        lineno=1, msg="test", args=(), exc_info=None
    )
    record.custom = "value"
    result = formatter.format(record)
    assert "custom" in result
    assert '"value"' in result
    # System attributes should not appear in extra fields
    assert "exc_text" not in result
    assert "relativeCreated" not in result
    assert "threadName" not in result


def test_invalid_log_level(tmp_path):
    with pytest.raises(ValueError, match="Invalid log level"):
        setup_logging(log_dir=str(tmp_path), level="INVALID")


def test_formatter_class():
    formatter = StructuredFormatter()
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="test.py",
        lineno=1, msg="test", args=(), exc_info=None
    )
    result = formatter.format(record)
    assert "[" in result  # timestamp
    assert "[INFO]" in result
    assert "test:1" in result