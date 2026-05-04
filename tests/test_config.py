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


def test_security_config_defaults():
    settings = Settings()
    assert settings.security.allowed_origins == ["*"]
    assert settings.security.require_authentication is False
    assert settings.security.api_key_header == "x-api-key"


def test_load_from_json_existing_file():
    settings = Settings.load_from_json()
    assert settings.openai.api_endpoint == "https://api.openai.com/v1"
    assert settings.proxy.max_retries == 3
    assert settings.security.api_key_header == "x-api-key"


def test_load_from_json_missing_file(monkeypatch):
    monkeypatch.setenv("SETTINGS_PATH", "/nonexistent/settings.json")
    settings = Settings.load_from_json()
    # Should return defaults when file doesn't exist
    assert settings.openai.api_endpoint == "https://api.openai.com/v1"