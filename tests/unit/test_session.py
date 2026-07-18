"""
Unit tests for DatabaseSessionManager and get_db dependency.
"""

from __future__ import annotations

import pytest

from app.core.settings import get_settings
from app.db.session import DatabaseSessionManager, get_db


@pytest.mark.asyncio
async def test_session_manager_uninitialised() -> None:
    """Methods must raise RuntimeError if manager is not initialised."""
    # Ensure it is closed
    await DatabaseSessionManager.close()

    with pytest.raises(RuntimeError) as excinfo:
        async with DatabaseSessionManager.connect():
            pass
    assert "not initialised" in str(excinfo.value)

    with pytest.raises(RuntimeError) as excinfo:
        async with DatabaseSessionManager.session():
            pass
    assert "not initialised" in str(excinfo.value)


@pytest.mark.asyncio
async def test_session_manager_lifecycle() -> None:
    """Manager lifecycle: init, double-init warning, connect, session commit/rollback, close."""
    settings = get_settings()
    test_db_url = "sqlite+aiosqlite:///:memory:"

    # 1. Initialize
    DatabaseSessionManager.init(test_db_url, settings=settings)
    assert DatabaseSessionManager._engine is not None
    assert DatabaseSessionManager._session_factory is not None

    # 2. Double-init should be skipped
    DatabaseSessionManager.init(test_db_url, settings=settings)

    # 3. Connect (DDL/Connection)
    async with DatabaseSessionManager.connect() as conn:
        assert conn is not None

    # 4. Session success (commits)
    async with DatabaseSessionManager.session() as sess:
        assert sess is not None

    # 5. Session failure (rolls back and re-raises)
    with pytest.raises(ValueError):
        async with DatabaseSessionManager.session():
            raise ValueError("Test rollback")

    # 6. Test get_db dependency
    db_gen = get_db()
    sess = await anext(db_gen)
    assert sess is not None
    # Clean up the generator
    try:
        await anext(db_gen)
    except StopAsyncIteration:
        pass

    # 7. Close
    await DatabaseSessionManager.close()
    assert DatabaseSessionManager._engine is None
    assert DatabaseSessionManager._session_factory is None
