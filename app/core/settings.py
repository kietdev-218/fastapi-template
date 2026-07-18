"""
Settings singleton accessor.

Provides a cached, application-wide settings instance via `get_settings()`.
Using `lru_cache` ensures the .env file is read exactly once at startup,
making it safe and efficient to call `get_settings()` anywhere in the codebase.

Usage::

    from app.core.settings import get_settings

    settings = get_settings()
    print(settings.app_name)
"""

from __future__ import annotations

from functools import lru_cache

from app.core.config import Settings


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the cached application settings instance.

    The first call reads and validates all environment variables. Subsequent
    calls return the cached instance without I/O overhead.

    Returns:
        Settings: The validated application settings singleton.

    Raises:
        ValidationError: If required environment variables are missing or invalid.
    """
    return Settings()  # type: ignore[call-arg]
