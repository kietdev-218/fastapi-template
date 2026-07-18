"""
Async SQLAlchemy engine and session management.

Provides:
- ``DatabaseSessionManager``: lifecycle manager for the async engine and session factory.
- ``get_db``: FastAPI dependency that yields a per-request ``AsyncSession``.

Design notes:
- The engine and session factory are created once during startup via
  ``DatabaseSessionManager.init()`` and disposed on shutdown via ``close()``.
- Each request gets its own ``AsyncSession`` that is committed on success
  and rolled back on exception, then always closed when the request ends.
- Follows the SQLAlchemy 2.x "async session" best practices.
"""

from __future__ import annotations

import contextlib
import logging
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

if TYPE_CHECKING:
    from app.core.config import Settings

logger = logging.getLogger(__name__)


class DatabaseSessionManager:
    """
    Manages the lifecycle of the SQLAlchemy async engine and session factory.

    Usage (in events.py)::

        DatabaseSessionManager.init(settings.async_database_url, settings=settings)
        ...
        await DatabaseSessionManager.close()
    """

    _engine: AsyncEngine | None = None
    _session_factory: async_sessionmaker[AsyncSession] | None = None

    @classmethod
    def init(cls, database_url: str, *, settings: Settings) -> None:
        """
        Initialise the async engine and session factory.

        Args:
            database_url: The async-compatible PostgreSQL DSN.
            settings: Application settings for pool configuration.
        """
        if cls._engine is not None:
            logger.warning("DatabaseSessionManager.init() called more than once — skipping.")
            return

        engine_kwargs: dict[str, Any] = {
            "echo": settings.db_echo,
            "pool_pre_ping": True,
        }

        # SQLite does not support pool configuration parameters
        if not database_url.startswith("sqlite"):
            engine_kwargs.update(
                {
                    "pool_size": settings.db_pool_size,
                    "max_overflow": settings.db_max_overflow,
                    "pool_timeout": settings.db_pool_timeout,
                    "pool_recycle": settings.db_pool_recycle,
                }
            )

        cls._engine = create_async_engine(database_url, **engine_kwargs)

        cls._session_factory = async_sessionmaker(
            cls._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        logger.debug("SQLAlchemy async engine created: %s", database_url)

    @classmethod
    async def close(cls) -> None:
        """Dispose the async engine and release all pooled connections."""
        if cls._engine is None:
            return

        await cls._engine.dispose()
        cls._engine = None
        cls._session_factory = None
        logger.debug("SQLAlchemy async engine disposed")

    @classmethod
    @contextlib.asynccontextmanager
    async def connect(cls) -> AsyncGenerator[AsyncConnection]:
        """
        Yield a raw async database connection.

        Useful for DDL operations (e.g., in Alembic migrations).
        """
        if cls._engine is None:
            raise RuntimeError("DatabaseSessionManager is not initialised. Call init() first.")

        async with cls._engine.begin() as conn:
            yield conn

    @classmethod
    @contextlib.asynccontextmanager
    async def session(cls) -> AsyncGenerator[AsyncSession]:
        """
        Yield a managed ``AsyncSession``.

        Commits on success, rolls back on exception, and always closes.
        """
        if cls._session_factory is None:
            raise RuntimeError("DatabaseSessionManager is not initialised. Call init() first.")

        async with cls._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


# --------------------------------------------------------------------------- #
# FastAPI Dependency
# --------------------------------------------------------------------------- #


async def get_db() -> AsyncGenerator[AsyncSession]:
    """
    FastAPI dependency that provides a per-request ``AsyncSession``.

    Commits the session on success and rolls back on any exception.
    Always closes the session when the request is done.

    Yields:
        An ``AsyncSession`` scoped to the current HTTP request.
    """
    async with DatabaseSessionManager.session() as session:
        yield session
