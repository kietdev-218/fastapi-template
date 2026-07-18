"""
Unit tests for the health check endpoint.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient
from pytest_mock import MockerFixture


@pytest.fixture
def mock_redis(mocker: MockerFixture) -> MagicMock:
    """Mock Redis client to return success on ping."""
    mock_client = MagicMock()
    mock_client.ping = AsyncMock(return_value=True)
    mocker.patch("app.core.redis.RedisManager.get_client", return_value=mock_client)
    return mock_client


@pytest.mark.asyncio
async def test_health_check_success(client: AsyncClient, mock_redis: MagicMock) -> None:
    """Health endpoint must return HTTP 200 and standard fields when healthy."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/health+json"

    data = response.json()
    assert data["success"] is True
    assert data["code"] == 0
    assert data["message"] == "Service is healthy"
    assert "timestamp" in data
    assert "traceId" in data

    health_data = data["data"]
    assert health_data["status"] == "pass"
    assert "version" in health_data
    assert "releaseId" in health_data
    assert "notes" in health_data
    assert "checks" in health_data

    db_checks = health_data["checks"]["database:connection"]
    assert len(db_checks) == 1
    assert db_checks[0]["status"] == "pass"
    assert db_checks[0]["componentType"] == "datastore"
    assert db_checks[0]["latencyMs"] is not None
    assert db_checks[0]["output"] is None

    redis_checks = health_data["checks"]["redis:connection"]
    assert len(redis_checks) == 1
    assert redis_checks[0]["status"] == "pass"
    assert redis_checks[0]["componentType"] == "cache"
    assert redis_checks[0]["latencyMs"] is not None
    assert redis_checks[0]["output"] is None


@pytest.mark.asyncio
async def test_health_check_db_failure(client: AsyncClient, mock_redis: MagicMock, mocker: MockerFixture) -> None:
    """Health endpoint must return HTTP 503 if database check fails."""
    # Mock the DB session's execute method to raise an exception
    mocker.patch("sqlalchemy.ext.asyncio.AsyncSession.execute", side_effect=Exception("DB connection error"))

    response = await client.get("/api/v1/health")
    assert response.status_code == 503
    assert response.headers["content-type"] == "application/health+json"

    data = response.json()
    assert data["success"] is False
    assert data["code"] == 503
    assert data["message"] == "Service is unhealthy"

    health_data = data["data"]
    assert health_data["status"] == "fail"

    db_checks = health_data["checks"]["database:connection"]
    assert db_checks[0]["status"] == "fail"
    assert "DB connection error" in db_checks[0]["output"]

    redis_checks = health_data["checks"]["redis:connection"]
    assert redis_checks[0]["status"] == "pass"


@pytest.mark.asyncio
async def test_health_check_redis_failure(client: AsyncClient, mock_redis: MagicMock) -> None:
    """Health endpoint must return HTTP 503 if Redis check fails."""
    # Make redis ping fail
    mock_redis.ping.side_effect = Exception("Redis connection refused")

    response = await client.get("/api/v1/health")
    assert response.status_code == 503
    assert response.headers["content-type"] == "application/health+json"

    data = response.json()
    assert data["success"] is False
    assert data["code"] == 503
    assert data["message"] == "Service is unhealthy"

    health_data = data["data"]
    assert health_data["status"] == "fail"

    db_checks = health_data["checks"]["database:connection"]
    assert db_checks[0]["status"] == "pass"

    redis_checks = health_data["checks"]["redis:connection"]
    assert redis_checks[0]["status"] == "fail"
    assert "Redis connection refused" in redis_checks[0]["output"]


@pytest.mark.asyncio
async def test_health_check_request_id_header(client: AsyncClient, mock_redis: MagicMock) -> None:
    """Health response must include X-Request-ID header."""
    response = await client.get("/api/v1/health")
    assert "x-request-id" in response.headers
