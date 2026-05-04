"""Tests for structured logging utility."""
from app.logger import get_logger, setup_logging


def test_get_logger():
    logger = get_logger("TestModule")
    assert logger.name == "TestModule"


def test_logger_format(tmp_path, caplog):
    setup_logging(log_dir=str(tmp_path))
    logger = get_logger("TestClass")
    with caplog.at_level("INFO"):
        logger.info("Test message")
    assert any("TestClass" in record.name for record in caplog.records)