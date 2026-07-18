"""
Core configuration module.

Defines the application Settings class using Pydantic BaseSettings,
providing type-safe, validated configuration sourced from environment
variables and .env files.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import (
    Field,
    computed_field,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All fields are type-safe and validated at startup. Settings are
    loaded from the environment or from a .env file in the project root.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------ #
    # Application
    # ------------------------------------------------------------------ #
    app_name: str = Field(default="FastAPI Microservice", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    app_description: str = Field(
        default="Production-ready FastAPI microservice",
        alias="APP_DESCRIPTION",
    )
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        alias="ENVIRONMENT",
    )
    debug: bool = Field(default=False, alias="DEBUG")

    # ------------------------------------------------------------------ #
    # Server
    # ------------------------------------------------------------------ #
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    workers: int = Field(default=1, alias="WORKERS")
    reload: bool = Field(default=False, alias="RELOAD")

    # ------------------------------------------------------------------ #
    # API
    # ------------------------------------------------------------------ #
    api_v1_str: str = Field(default="/api/v1", alias="API_V1_STR")

    # ------------------------------------------------------------------ #
    # Security
    # ------------------------------------------------------------------ #
    secret_key: str = Field(
        default="INSECURE-DEV-DEFAULT-CHANGE-ME-BEFORE-DEPLOYING-TO-PRODUCTION",
        alias="SECRET_KEY",
        description="Secret key for JWT signing. MUST be changed in production.",
    )
    jwks_url: str = Field(
        default="http://oathkeeper:4456/.well-known/jwks.json",
        alias="JWKS_URL",
        description="URL to fetch the JSON Web Key Set for verifying tokens from Oathkeeper.",
    )
    algorithm: str = Field(default="RS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    refresh_token_expire_days: int = Field(
        default=7,
        alias="REFRESH_TOKEN_EXPIRE_DAYS",
    )

    # Oathkeeper-compatible JWT fields
    # jwt_issuer must match `trusted_issuers` in Oathkeeper's `jwt` authenticator config.
    jwt_issuer: str = Field(
        default="http://localhost:8000",
        alias="JWT_ISSUER",
        description="Value of the 'iss' claim. Must match Oathkeeper's trusted_issuers list.",
    )
    # jwt_audience must match `target_audience` in Oathkeeper's `jwt` authenticator config.
    jwt_audience: list[str] | str = Field(
        default=["http://localhost:8000"],
        alias="JWT_AUDIENCE",
        description="Value(s) of the 'aud' claim. Must match Oathkeeper's target_audience list.",
    )

    # ------------------------------------------------------------------ #
    # Database (PostgreSQL)
    # ------------------------------------------------------------------ #
    postgres_server: str = Field(default="localhost", alias="POSTGRES_SERVER")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_user: str = Field(default="postgres", alias="POSTGRES_USER")
    postgres_password: str = Field(default="postgres", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="fastapi_db", alias="POSTGRES_DB")

    # Optional override: takes precedence over individual POSTGRES_* vars
    database_url: str | None = Field(default=None, alias="DATABASE_URL")

    # ------------------------------------------------------------------ #
    # Redis
    # ------------------------------------------------------------------ #
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")
    redis_password: str | None = Field(default=None, alias="REDIS_PASSWORD")

    # Pool settings
    db_pool_size: int = Field(default=10, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=20, alias="DB_MAX_OVERFLOW")
    db_pool_timeout: int = Field(default=30, alias="DB_POOL_TIMEOUT")
    db_pool_recycle: int = Field(default=3600, alias="DB_POOL_RECYCLE")
    db_echo: bool = Field(default=False, alias="DB_ECHO")

    # ------------------------------------------------------------------ #
    # CORS
    # ------------------------------------------------------------------ #
    cors_origins: str = Field(
        default="http://localhost:3000",
        alias="CORS_ORIGINS",
        description="Comma-separated list of allowed CORS origins.",
    )
    cors_allow_credentials: bool = Field(default=True, alias="CORS_ALLOW_CREDENTIALS")

    # ------------------------------------------------------------------ #
    # Logging
    # ------------------------------------------------------------------ #
    log_level: str = Field(
        default="INFO",
        alias="LOG_LEVEL",
        description="Logging level — case-insensitive, normalised to uppercase.",
    )
    log_format: Literal["json", "text"] = Field(default="json", alias="LOG_FORMAT")

    @field_validator("log_level", mode="before")
    @classmethod
    def normalise_log_level(cls, v: str) -> str:
        """Accept any case ('info', 'Info', 'INFO') and normalise to uppercase."""
        upper = v.upper()
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if upper not in valid:
            raise ValueError(f"log_level must be one of {valid}, got '{v}'")
        return upper

    @field_validator("jwt_audience", mode="before")
    @classmethod
    def parse_jwt_audience(cls, v: str | list[Any]) -> list[str]:
        """Accept a comma-separated string or a JSON array for JWT_AUDIENCE.

        This allows the env var to be written as either::

            JWT_AUDIENCE="https://api.example.com,https://other.example.com"
            JWT_AUDIENCE=["https://api.example.com"]
        """
        if isinstance(v, list):
            return [str(item) for item in v]
        import json

        try:
            parsed = json.loads(v)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        except (json.JSONDecodeError, TypeError):
            pass
        return [item.strip() for item in v.split(",") if item.strip()]

    log_file: str | None = Field(default=None, alias="LOG_FILE")

    # ------------------------------------------------------------------ #
    # Computed Fields
    # ------------------------------------------------------------------ #
    @computed_field  # type: ignore[prop-decorator]
    @property
    def redis_url(self) -> str:
        """
        Return the Redis DSN.
        """
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def async_database_url(self) -> str:
        """
        Return the async-compatible PostgreSQL DSN.

        Uses the explicit DATABASE_URL if provided; otherwise constructs
        the DSN from individual POSTGRES_* environment variables.
        """
        if self.database_url:
            # Ensure the scheme is asyncpg-compatible
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://").replace(
                "postgres://", "postgresql+asyncpg://"
            )

        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_server}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sync_database_url(self) -> str:
        """
        Return a synchronous PostgreSQL DSN (used by Alembic migrations).
        """
        return self.async_database_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origins_list(self) -> list[str]:
        """
        Return CORS_ORIGINS as a parsed list.

        Splits a comma-separated string so that the field can be written
        as a plain env-var value (e.g. ``CORS_ORIGINS=http://a.com,http://b.com``)
        without requiring JSON encoding.
        """
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # ------------------------------------------------------------------ #
    # Validators
    # ------------------------------------------------------------------ #
    @model_validator(mode="after")
    def validate_secret_key_in_production(self) -> Settings:
        """Prevent startup with the insecure default secret key in production."""
        insecure_default = "INSECURE-DEV-DEFAULT-CHANGE-ME-BEFORE-DEPLOYING-TO-PRODUCTION"
        if self.environment == "production" and self.secret_key == insecure_default:
            raise ValueError(
                "SECRET_KEY must be set to a secure random value in production. "
                'Generate one with: python -c "import secrets; print(secrets.token_urlsafe(64))"'
            )
        return self

    # ------------------------------------------------------------------ #
    # Convenience helpers
    # ------------------------------------------------------------------ #
    @property
    def is_development(self) -> bool:
        """Return True when running in development mode."""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Return True when running in production mode."""
        return self.environment == "production"
