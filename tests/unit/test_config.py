"""
Unit tests for application configuration settings.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_default_and_computed_fields() -> None:
    """Settings should correctly compute async and sync database urls."""
    settings = Settings(
        POSTGRES_SERVER="localhost",
        POSTGRES_PORT=5432,
        POSTGRES_USER="postgres",
        POSTGRES_PASSWORD="password",  # pragma: allowlist secret
        POSTGRES_DB="app",
    )
    assert (
        settings.async_database_url
        == "postgresql+asyncpg://postgres:password@localhost:5432/app"  # pragma: allowlist secret
    )
    assert (
        settings.sync_database_url
        == "postgresql+psycopg2://postgres:password@localhost:5432/app"  # pragma: allowlist secret
    )


def test_settings_with_explicit_database_url() -> None:
    """Settings should use explicit DATABASE_URL if provided."""
    url = "postgresql://user:pass@host:5432/db"  # pragma: allowlist secret
    settings = Settings(DATABASE_URL=url)
    assert settings.async_database_url == "postgresql+asyncpg://user:pass@host:5432/db"  # pragma: allowlist secret


def test_jwt_audience_parsing() -> None:
    """Settings should parse comma-separated string or list for JWT_AUDIENCE."""
    # List format
    settings_list = Settings(JWT_AUDIENCE=["aud1", "aud2"])
    assert settings_list.jwt_audience == ["aud1", "aud2"]

    # Comma-separated format
    settings_str = Settings(JWT_AUDIENCE="aud1, aud2")
    assert settings_str.jwt_audience == ["aud1", "aud2"]

    # JSON array format
    settings_json = Settings(JWT_AUDIENCE='["aud1", "aud2"]')
    assert settings_json.jwt_audience == ["aud1", "aud2"]


def test_production_secret_key_validation() -> None:
    """Settings must raise validation error if default secret key is used in production."""
    with pytest.raises(ValidationError) as excinfo:
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="INSECURE-DEV-DEFAULT-CHANGE-ME-BEFORE-DEPLOYING-TO-PRODUCTION",  # pragma: allowlist secret
        )
    assert "SECRET_KEY must be set" in str(excinfo.value)
