from functools import lru_cache
from pathlib import Path
from urllib.parse import unquote, urlsplit

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from apps.api.app.secrets.provider import (
    ManagedSecretProvider,
    MountedFileSecretProvider,
    SecretProviderError,
    is_placeholder_secret,
    local_ephemeral_secret,
)


class Settings(BaseSettings):
    secret_provider_mode: str = Field(
        default="environment",
        pattern="^(environment|mounted_files|managed)$",
        validation_alias=AliasChoices("SECRET_PROVIDER_MODE", "secret_provider_mode"),
    )
    secret_mount_dir: str = Field(
        default="/run/secrets",
        validation_alias=AliasChoices("SECRET_MOUNT_DIR", "secret_mount_dir"),
    )
    app_environment: str = Field(
        default="local",
        pattern="^(local|development|test|production)$",
        validation_alias=AliasChoices("APP_ENVIRONMENT", "app_environment"),
    )
    auth_mode: str = Field(
        default="local_demo",
        pattern="^(local_demo|oidc_fixture|oidc)$",
        validation_alias=AliasChoices("AUTH_MODE", "auth_mode"),
    )
    oidc_issuer: str = Field(
        default="https://identity.local.proofbase.invalid",
        validation_alias=AliasChoices("OIDC_ISSUER", "oidc_issuer"),
    )
    oidc_audience: str = Field(
        default="proofbase-api",
        validation_alias=AliasChoices("OIDC_AUDIENCE", "oidc_audience"),
    )
    oidc_local_signing_secret: str = Field(
        default="",
        repr=False,
        validation_alias=AliasChoices("OIDC_LOCAL_SIGNING_SECRET", "oidc_local_signing_secret"),
    )
    oidc_future_provider: str = Field(
        default="microsoft_entra_id",
        validation_alias=AliasChoices("OIDC_FUTURE_PROVIDER", "oidc_future_provider"),
    )
    session_absolute_minutes: int = Field(
        default=480,
        ge=5,
        le=1440,
        validation_alias=AliasChoices("SESSION_ABSOLUTE_MINUTES", "session_absolute_minutes"),
    )
    session_idle_minutes: int = Field(
        default=30,
        ge=5,
        le=240,
        validation_alias=AliasChoices("SESSION_IDLE_MINUTES", "session_idle_minutes"),
    )
    default_demo_tenant_id: str = Field(
        default="00000000-0000-0000-0000-000000002801",
        validation_alias=AliasChoices("DEFAULT_DEMO_TENANT_ID", "default_demo_tenant_id"),
    )
    database_enforce_rls: bool = Field(
        default=True,
        validation_alias=AliasChoices("DATABASE_ENFORCE_RLS", "database_enforce_rls"),
    )
    database_runtime_role: str = Field(
        default="proofbase_runtime",
        pattern="^[a-z_][a-z0-9_]{0,62}$",
        validation_alias=AliasChoices("DATABASE_RUNTIME_ROLE", "database_runtime_role"),
    )
    database_url: str = Field(default="postgresql://postgres:postgres@localhost:5432/enterprise_knowledge_agent", repr=False)
    rate_limit_backend: str = Field(
        default="memory",
        pattern="^(memory|redis)$",
        validation_alias=AliasChoices("RATE_LIMIT_BACKEND", "rate_limit_backend"),
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        repr=False,
        validation_alias=AliasChoices("REDIS_URL", "redis_url"),
    )
    max_request_bytes: int = Field(default=12_000_000, ge=1024, le=25_000_000)
    max_question_chars: int = Field(default=4_000, ge=100, le=4_000)
    tenant_daily_ai_budget_usd: float = Field(default=5.0, gt=0, le=10_000)
    external_ai_max_retries: int = Field(default=1, ge=0, le=2)
    file_quarantine_dir: str = "data/quarantine"
    file_max_bytes: int = Field(default=10 * 1024 * 1024, ge=1024, le=10 * 1024 * 1024)
    file_max_pages: int = Field(default=100, ge=1, le=100)
    file_max_extracted_chars: int = Field(default=2_000_000, ge=10_000, le=2_000_000)
    file_max_expansion_ratio: int = Field(default=200, ge=10, le=500)
    file_parser_timeout_seconds: int = Field(default=15, ge=1, le=60)
    file_parser_mode: str = Field(default="subprocess", pattern="^(subprocess|isolated_worker)$")
    file_scanner_mode: str = Field(default="fixture_signature", pattern="^(fixture_signature|hosted)$")
    file_quarantine_retention_days: int = Field(default=7, ge=1, le=7)
    file_approved_original_retention_days: int = Field(default=30, ge=1, le=30)
    file_access_signing_secret: str = Field(default="", repr=False)
    file_access_signing_secret_file: str = ""
    openai_api_key: str = Field(
        default="",
        repr=False,
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
    request_assessment_mode: str = Field(
        default="semantic_all_remaining",
        pattern="^(deterministic_only|semantic_uncertain_only|semantic_all_remaining)$",
        validation_alias=AliasChoices("REQUEST_ASSESSMENT_MODE", "request_assessment_mode"),
    )
    request_assessment_model: str = Field(
        default="gpt-4.1-mini",
        validation_alias=AliasChoices("REQUEST_ASSESSMENT_MODEL", "request_assessment_model"),
    )
    request_assessment_prompt_version: str = Field(
        default="v2",
        validation_alias=AliasChoices(
            "REQUEST_ASSESSMENT_PROMPT_VERSION",
            "request_assessment_prompt_version",
        ),
    )
    request_assessment_timeout_seconds: float = Field(
        default=8.0,
        ge=1.0,
        le=30.0,
        validation_alias=AliasChoices(
            "REQUEST_ASSESSMENT_TIMEOUT_SECONDS",
            "request_assessment_timeout_seconds",
        ),
    )
    evidence_assessment_mode: str = Field(
        default="hybrid",
        pattern="^(deterministic_only|hybrid|semantic_always)$",
        validation_alias=AliasChoices("EVIDENCE_ASSESSMENT_MODE", "evidence_assessment_mode"),
    )
    evidence_assessment_model: str = Field(
        default="gpt-4.1-mini",
        validation_alias=AliasChoices("EVIDENCE_ASSESSMENT_MODEL", "evidence_assessment_model"),
    )
    evidence_assessment_prompt_version: str = Field(
        default="v2",
        validation_alias=AliasChoices(
            "EVIDENCE_ASSESSMENT_PROMPT_VERSION",
            "evidence_assessment_prompt_version",
        ),
    )
    evidence_assessment_timeout_seconds: float = Field(
        default=15.0,
        ge=1.0,
        le=30.0,
        validation_alias=AliasChoices(
            "EVIDENCE_ASSESSMENT_TIMEOUT_SECONDS",
            "evidence_assessment_timeout_seconds",
        ),
    )
    post_generation_validation_model: str = Field(
        default="gpt-4.1-mini",
        validation_alias=AliasChoices(
            "POST_GENERATION_VALIDATION_MODEL",
            "post_generation_validation_model",
        ),
    )
    post_generation_validation_prompt_version: str = Field(
        default="v2",
        validation_alias=AliasChoices(
            "POST_GENERATION_VALIDATION_PROMPT_VERSION",
            "post_generation_validation_prompt_version",
        ),
    )
    post_generation_validation_timeout_seconds: float = Field(
        default=30.0,
        ge=1.0,
        le=30.0,
        validation_alias=AliasChoices(
            "POST_GENERATION_VALIDATION_TIMEOUT_SECONDS",
            "post_generation_validation_timeout_seconds",
        ),
    )
    default_top_k: int = 5
    log_level: str = "INFO"
    observability_log_path: str = "data/observability/request-logs.jsonl"
    audit_log_path: str = "data/audit/audit-events.jsonl"
    observability_retention_days: int = Field(default=30, ge=1, le=365)
    audit_retention_days: int = Field(default=365, ge=30, le=2555)
    incident_evidence_hold: bool = False
    security_event_sink_mode: str = Field(default="local_jsonl", pattern="^(local_jsonl|external)$")
    security_event_log_path: str = "data/security/security-events.jsonl"
    security_notification_log_path: str = "data/security/local-notifications.jsonl"
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
        repr=False,
        validation_alias=AliasChoices("PROOFBASE_TELEMETRY_API_KEY", "proofbase_telemetry_api_key"),
    )
    proofbase_telemetry_api_key_file: str = Field(
        default="",
        validation_alias=AliasChoices("PROOFBASE_TELEMETRY_API_KEY_FILE", "proofbase_telemetry_api_key_file"),
    )
    proofbase_telemetry_timeout_seconds: float = Field(
        default=2.0,
        validation_alias=AliasChoices(
            "PROOFBASE_TELEMETRY_TIMEOUT_SECONDS",
            "proofbase_telemetry_timeout_seconds",
        ),
    )
    proofbase_telemetry_max_metadata_bytes: int = Field(
        default=2048,
        validation_alias=AliasChoices(
            "PROOFBASE_TELEMETRY_MAX_METADATA_BYTES",
            "proofbase_telemetry_max_metadata_bytes",
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
        hide_input_in_errors=True,
    )

    @model_validator(mode="after")
    def load_runtime_secrets(self) -> "Settings":
        if self.secret_provider_mode == "mounted_files":
            provider = MountedFileSecretProvider(self.secret_mount_dir)
            try:
                mounted_openai = provider.get("openai_api_key")
                mounted_file_signing = provider.get("file_access_signing_secret")
                mounted_telemetry = provider.get("proofbase_telemetry_api_key")
                if self.app_environment == "production":
                    self.openai_api_key = mounted_openai or ""
                    self.file_access_signing_secret = mounted_file_signing or ""
                    self.proofbase_telemetry_api_key = mounted_telemetry or ""
                else:
                    self.openai_api_key = mounted_openai or self.openai_api_key
                    self.file_access_signing_secret = mounted_file_signing or self.file_access_signing_secret
                    self.proofbase_telemetry_api_key = mounted_telemetry or self.proofbase_telemetry_api_key
            except SecretProviderError:
                if self.app_environment == "production":
                    raise ValueError("A required mounted secret could not be read.") from None
        elif self.secret_provider_mode == "managed":
            try:
                ManagedSecretProvider().get("startup_probe")
            except SecretProviderError:
                if self.app_environment == "production":
                    raise ValueError("Managed secret provider is selected but no adapter is connected.") from None

        self.openai_api_key = self.openai_api_key or _read_secret_file(self.openai_api_key_file)
        self.file_access_signing_secret = self.file_access_signing_secret or _read_secret_file(self.file_access_signing_secret_file)
        self.proofbase_telemetry_api_key = self.proofbase_telemetry_api_key or _read_secret_file(self.proofbase_telemetry_api_key_file)
        if self.app_environment != "production" and not self.file_access_signing_secret:
            self.file_access_signing_secret = local_ephemeral_secret("file_access_signing")
        return self

    @model_validator(mode="after")
    def reject_unsafe_production_identity(self) -> "Settings":
        if self.app_environment == "production" and self.auth_mode in {"local_demo", "oidc_fixture"}:
            raise ValueError("Production requires AUTH_MODE=oidc; demo and local fixture identities are forbidden.")
        database_user = unquote(urlsplit(self.database_url).username or "")
        if self.app_environment == "production" and database_user.lower() == "postgres":
            raise ValueError("Production DATABASE_URL must not use the PostgreSQL superuser.")
        if self.app_environment == "production" and not self.database_enforce_rls:
            raise ValueError("Production requires DATABASE_ENFORCE_RLS=true.")
        if self.app_environment == "production" and self.rate_limit_backend != "redis":
            raise ValueError("Production requires RATE_LIMIT_BACKEND=redis or a reviewed shared-store adapter.")
        if self.app_environment == "production" and self.file_parser_mode != "isolated_worker":
            raise ValueError("Production requires an isolated file-parser worker.")
        if self.app_environment == "production" and self.file_scanner_mode != "hosted":
            raise ValueError("Production requires a connected malware-scanner adapter.")
        if self.app_environment == "production" and self.secret_provider_mode == "environment":
            raise ValueError("Production rejects environment-only secrets; use mounted_files or a connected managed provider.")
        if self.app_environment == "production" and self.security_event_sink_mode != "external":
            raise ValueError("Production requires a connected external security-event sink.")
        if self.app_environment == "production":
            if is_placeholder_secret(self.openai_api_key):
                raise ValueError("Production requires a non-placeholder OpenAI credential from the selected secret provider.")
            if len(self.file_access_signing_secret) < 32 or is_placeholder_secret(self.file_access_signing_secret):
                raise ValueError("Production requires a non-placeholder file-access signing secret of at least 32 characters.")
            database_password = unquote(urlsplit(self.database_url).password or "")
            if is_placeholder_secret(database_password):
                raise ValueError("Production DATABASE_URL requires a non-placeholder runtime credential.")
            redis = urlsplit(self.redis_url)
            if redis.scheme != "rediss" or is_placeholder_secret(unquote(redis.password or "")):
                raise ValueError("Production Redis requires TLS and a non-placeholder credential.")
            if self.proofbase_telemetry_enabled and is_placeholder_secret(self.proofbase_telemetry_api_key):
                raise ValueError("Enabled production telemetry requires a non-placeholder credential.")
            if self.security_event_sink_mode == "external":
                raise ValueError("External security-event sink is selected but no destination adapter is connected.")
        if self.auth_mode == "oidc_fixture" and len(self.oidc_local_signing_secret.encode("utf-8")) < 32:
            raise ValueError("OIDC fixture mode requires an OIDC_LOCAL_SIGNING_SECRET of at least 32 bytes.")
        if self.session_idle_minutes >= self.session_absolute_minutes:
            raise ValueError("SESSION_IDLE_MINUTES must be shorter than SESSION_ABSOLUTE_MINUTES.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


def _read_secret_file(path_value: str) -> str:
    if not path_value:
        return ""
    try:
        path = Path(path_value)
        if path.stat().st_size > 16_384:
            return ""
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""
