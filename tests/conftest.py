"""
Test configuration and shared fixtures.

Provides:
- An async test client backed by the FastAPI application.
- An isolated in-memory (SQLite) database session for unit tests.
- Factory fixtures for creating test users and items.

All fixtures use ``pytest-asyncio`` in ``auto`` mode so that async test
functions are handled transparently.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from main import create_application
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.db.base_class import Base
from app.db.session import get_db

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# --------------------------------------------------------------------------- #
# Database Fixtures
# --------------------------------------------------------------------------- #


@pytest_asyncio.fixture(scope="session")
async def test_engine() -> AsyncGenerator[AsyncEngine]:
    """
    Create a shared async engine backed by an in-memory SQLite database.

    Scope is ``session`` so the engine is created once per test run.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession]:
    """
    Provide an isolated ``AsyncSession`` per test.

    Each test gets a fresh session that is rolled back after the test
    completes, keeping tests independent from each other.
    """
    session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with session_factory() as session:
        yield session
        await session.rollback()


# --------------------------------------------------------------------------- #
# Application Fixtures
# --------------------------------------------------------------------------- #


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    """
    Provide an ``AsyncClient`` for the FastAPI test application.

    The ``get_db`` dependency is overridden to use the test session so
    that all database operations occur within the test transaction.
    """
    app = create_application()

    async def override_get_db() -> AsyncGenerator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac


# --------------------------------------------------------------------------- #
# Data Factory Fixtures
# --------------------------------------------------------------------------- #


@pytest.fixture
def user_create_data() -> dict[str, Any]:
    """Return valid data for creating a test user."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "SecureP@ss1",  # pragma: allowlist secret
        "full_name": "Test User",
    }


@pytest.fixture
def item_create_data() -> dict[str, Any]:
    """Return valid data for creating a test item."""
    return {
        "title": "Test Item",
        "description": "A test item description.",
        "price": 9.99,
        "is_active": True,
    }
