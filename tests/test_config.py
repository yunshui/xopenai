"""Configuration tests."""
import os
import pytest
from app.config import Settings


def test_default_settings():
    settings = Settings()
    assert settings.openai.api_endpoint == "https://api.openai.com/v1"
    assert settings.proxy.max_retries == 3


def test_env_override(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    settings = Settings()
    assert settings.openai.api_key == "test-key"
    assert settings.logging.level == "DEBUG"