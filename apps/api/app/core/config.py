from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/enterprise_knowledge_agent"
    openai_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("OPENAI_API_KEY", "openai_api_key"),
    )
    openai_api_key_file: str = Field(
        default="",
        validation_alias=AliasChoices("OPENAI_API_KEY_FILE", "openai_api_key_file"),
    )
    openai_embedding_model: str = "text-embedding-3-small"
    openai_chat_model: str = Field(
        default="gpt-4.1-mini",
        validation_alias=AliasChoices("OPENAI_CHAT_MODEL", "OPENAI_MODEL"),
    )
    default_top_k: int = 5
    log_level: str = "INFO"
    observability_log_path: str = "data/observability/request-logs.jsonl"
    audit_log_path: str = "data/audit/audit-events.jsonl"
    upload_storage_dir: str = "data/uploads"
    default_demo_user_id: str = "00000000-0000-0000-0000-000000002701"
    proofbase_telemetry_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices("PROOFBASE_TELEMETRY_ENABLED", "proofbase_telemetry_enabled"),
    )
    proofbase_telemetry_endpoint: str = Field(
        default="http://localhost:8000/v1/usage/llm-events",
        validation_alias=AliasChoices("PROOFBASE_TELEMETRY_ENDPOINT", "proofbase_telemetry_endpoint"),
    )
    proofbase_telemetry_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("PROOFBASE_TELEMETRY_API_KEY", "proofbase_telemetry_api_key"),
    )
    proofbase_telemetry_timeout_seconds: float = Field(
        default=2.0,
        validation_alias=AliasChoices(
            "PROOFBASE_TELEMETRY_TIMEOUT_SECONDS",
            "proofbase_telemetry_timeout_seconds",
        ),
    )
    proofbase_telemetry_redact_content: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "PROOFBASE_TELEMETRY_REDACT_CONTENT",
            "proofbase_telemetry_redact_content",
        ),
    )
    cors_allowed_origins: str = (
        "http://localhost:3000,"
        "http://127.0.0.1:3000,"
        "http://localhost:3001,"
        "http://127.0.0.1:3001"
    )

    model_config = SettingsConfigDict(
        env_file=(".env", "apps/api/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def load_openai_api_key_file(self) -> "Settings":
        if self.openai_api_key or not self.openai_api_key_file:
            return self
        try:
            self.openai_api_key = Path(self.openai_api_key_file).read_text(encoding="utf-8").strip()
        except OSError:
            self.openai_api_key = ""
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
