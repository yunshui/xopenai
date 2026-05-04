"""Configuration management."""
import os
from typing import Optional
from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel as PydanticBaseModel


class OpenAIConfig(PydanticBaseModel):
    api_endpoint: str = "https://api.openai.com/v1"
    api_key: str = ""


class ProxyConfig(PydanticBaseModel):
    max_retries: int = 3
    timeout: int = 30
    retry_delay: float = 1.0
    retry_backoff_multiplier: float = 2.0
    max_concurrent_requests: int = 50
    rate_limit_per_minute: int = 100
    max_request_size_mb: int = 10


class LoggingConfig(PydanticBaseModel):
    level: str = "INFO"
    log_dir: str = "logs"


class SecurityConfig(PydanticBaseModel):
    allowed_origins: list[str] = ["*"]
    require_authentication: bool = False
    api_key_header: str = "x-api-key"


class Settings(BaseSettings):
    openai_api_endpoint: str = Field(default="https://api.openai.com/v1", alias="openai__api_endpoint", validation_alias="openai__api_endpoint", serialization_alias="openai__api_endpoint")
    openai_api_key: str = Field(default="", alias="openai__api_key", validation_alias="openai__api_key", serialization_alias="openai__api_key")
    proxy_max_retries: int = Field(default=3, alias="proxy__max_retries", validation_alias="proxy__max_retries", serialization_alias="proxy__max_retries")
    proxy_timeout: int = Field(default=30, alias="proxy__timeout", validation_alias="proxy__timeout", serialization_alias="proxy__timeout")
    proxy_retry_delay: float = Field(default=1.0, alias="proxy__retry_delay", validation_alias="proxy__retry_delay", serialization_alias="proxy__retry_delay")
    proxy_retry_backoff_multiplier: float = Field(default=2.0, alias="proxy__retry_backoff_multiplier", validation_alias="proxy__retry_backoff_multiplier", serialization_alias="proxy__retry_backoff_multiplier")
    proxy_max_concurrent_requests: int = Field(default=50, alias="proxy__max_concurrent_requests", validation_alias="proxy__max_concurrent_requests", serialization_alias="proxy__max_concurrent_requests")
    proxy_rate_limit_per_minute: int = Field(default=100, alias="proxy__rate_limit_per_minute", validation_alias="proxy__rate_limit_per_minute", serialization_alias="proxy__rate_limit_per_minute")
    proxy_max_request_size_mb: int = Field(default=10, alias="proxy__max_request_size_mb", validation_alias="proxy__max_request_size_mb", serialization_alias="proxy__max_request_size_mb")
    logging_level: str = Field(default="INFO", validation_alias=AliasChoices("logging__level", "log_level"), serialization_alias="logging__level")
    logging_log_dir: str = Field(default="logs", alias="logging__log_dir", validation_alias="logging__log_dir", serialization_alias="logging__log_dir")
    model_mapping: dict[str, str] = Field(default_factory=dict)
    security_allowed_origins: list[str] = Field(default=["*"], alias="security__allowed_origins", validation_alias="security__allowed_origins", serialization_alias="security__allowed_origins")
    security_require_authentication: bool = Field(default=False, alias="security__require_authentication", validation_alias="security__require_authentication", serialization_alias="security__require_authentication")
    security_api_key_header: str = Field(default="x-api-key", alias="security__api_key_header", validation_alias="security__api_key_header", serialization_alias="security__api_key_header")

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_file=".env",
        populate_by_name=True,
    )

    @property
    def openai(self) -> OpenAIConfig:
        return OpenAIConfig(
            api_endpoint=self.openai_api_endpoint,
            api_key=self.openai_api_key,
        )

    @property
    def proxy(self) -> ProxyConfig:
        return ProxyConfig(
            max_retries=self.proxy_max_retries,
            timeout=self.proxy_timeout,
            retry_delay=self.proxy_retry_delay,
            retry_backoff_multiplier=self.proxy_retry_backoff_multiplier,
            max_concurrent_requests=self.proxy_max_concurrent_requests,
            rate_limit_per_minute=self.proxy_rate_limit_per_minute,
            max_request_size_mb=self.proxy_max_request_size_mb,
        )

    @property
    def logging(self) -> LoggingConfig:
        return LoggingConfig(
            level=self.logging_level,
            log_dir=self.logging_log_dir,
        )

    @property
    def security(self) -> SecurityConfig:
        return SecurityConfig(
            allowed_origins=self.security_allowed_origins,
            require_authentication=self.security_require_authentication,
            api_key_header=self.security_api_key_header,
        )

    @classmethod
    def load_from_json(cls, path: Optional[str] = None) -> "Settings":
        from pathlib import Path
        import json
        if path is None:
            path = os.getenv("SETTINGS_PATH", "conf/settings.json")
        json_path = Path(path)
        if not json_path.exists():
            return cls()
        with open(json_path) as f:
            data = json.load(f)

        # Flatten nested JSON data to match flat field names
        # Don't flatten dict fields like model_mapping
        dict_fields = {'model_mapping'}
        flat_data = {}
        for key, value in data.items():
            if key in dict_fields:
                flat_data[key] = value
            elif isinstance(value, dict):
                for subkey, subvalue in value.items():
                    flat_key = f"{key}__{subkey}"
                    flat_data[flat_key] = subvalue
            else:
                flat_data[key] = value
        return cls(**flat_data)