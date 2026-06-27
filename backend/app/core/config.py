from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, PositiveInt, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ENV_PATH = BACKEND_ROOT / ".env"


class ConfigurationError(Exception):
    """Safe configuration error that never contains secret values."""

    def __init__(self, message: str, *, variable_name: str | None = None) -> None:
        super().__init__(message)
        self.variable_name = variable_name


class MissingConfigurationError(ConfigurationError):
    """Raised when a live provider setting is required but absent."""


class UnknownModelRoleError(ConfigurationError):
    """Raised when model routing receives an unsupported role."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_ENV_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    app_env: str = Field(default="development", validation_alias="APP_ENV")
    app_version: str = Field(default="0.1.0", validation_alias="APP_VERSION")
    host: str = Field(default="0.0.0.0", validation_alias="HOST")
    port: PositiveInt = Field(default=8000, validation_alias="PORT")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    max_input_characters: PositiveInt = Field(
        default=12000,
        validation_alias="MAX_INPUT_CHARACTERS",
    )
    mock_mode: bool = Field(default=True, validation_alias="MOCK_MODE")
    enable_web_search: bool = Field(default=True, validation_alias="ENABLE_WEB_SEARCH")
    enable_virustotal: bool = Field(default=False, validation_alias="ENABLE_VIRUSTOTAL")
    provider_timeout_seconds: PositiveInt = Field(
        default=20,
        validation_alias="PROVIDER_TIMEOUT_SECONDS",
    )
    max_search_queries: PositiveInt = Field(default=3, validation_alias="MAX_SEARCH_QUERIES")
    max_evidence_items: PositiveInt = Field(default=8, validation_alias="MAX_EVIDENCE_ITEMS")
    cors_allow_origins_value: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        validation_alias=AliasChoices("CORS_ALLOW_ORIGINS", "FRONTEND_ORIGIN"),
        exclude=True,
    )

    openai_api_key: SecretStr | None = Field(
        default=None,
        validation_alias="OPENAI_API_KEY",
        repr=False,
        exclude=True,
    )
    openai_model_fast: str | None = Field(default=None, validation_alias="OPENAI_MODEL_FAST")
    openai_model_expert: str | None = Field(default=None, validation_alias="OPENAI_MODEL_EXPERT")
    openai_model_judge: str | None = Field(default=None, validation_alias="OPENAI_MODEL_JUDGE")
    openai_model_report: str | None = Field(default=None, validation_alias="OPENAI_MODEL_REPORT")
    tavily_api_key: SecretStr | None = Field(
        default=None,
        validation_alias="TAVILY_API_KEY",
        repr=False,
        exclude=True,
    )
    virustotal_api_key: SecretStr | None = Field(
        default=None,
        validation_alias="VIRUSTOTAL_API_KEY",
        repr=False,
        exclude=True,
    )
    run_live_provider_tests: bool = Field(default=False, validation_alias="RUN_LIVE_PROVIDER_TESTS")

    @property
    def cors_allow_origins(self) -> tuple[str, ...]:
        return tuple(
            item.strip()
            for item in self.cors_allow_origins_value.split(",")
            if item.strip()
        )

    @property
    def loaded_env_file(self) -> Path:
        return BACKEND_ENV_PATH

    def provider_timeout_float(self) -> float:
        return float(self.provider_timeout_seconds)


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()


settings = get_settings()
