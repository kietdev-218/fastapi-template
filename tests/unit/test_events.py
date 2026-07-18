"""
Unit tests for application lifecycle events.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI

from app.core.events import lifespan
from app.db.session import DatabaseSessionManager


@pytest.mark.asyncio
async def test_application_lifespan() -> None:
    """The lifespan context manager must handle startup and shutdown successfully."""
    # Ensure any active connections are closed before running lifespan test
    await DatabaseSessionManager.close()

    app = FastAPI()
    async with lifespan(app):
        # Startup phase should have initialized the engine
        assert DatabaseSessionManager._engine is not None
        assert DatabaseSessionManager._session_factory is not None

    # Shutdown phase should have cleaned up the engine
    assert DatabaseSessionManager._engine is None
    assert DatabaseSessionManager._session_factory is None
