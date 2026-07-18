"""
Unit test for the health check endpoint.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check_returns_200(client: AsyncClient) -> None:
    """Health endpoint must return HTTP 200."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_check_response_shape(client: AsyncClient) -> None:
    """Health response must include all required fields."""
    response = await client.get("/api/v1/health")
    data = response.json()

    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data
    assert "timestamp" in data
    assert "environment" in data


@pytest.mark.asyncio
async def test_health_check_request_id_header(client: AsyncClient) -> None:
    """Health response must include X-Request-ID header."""
    response = await client.get("/api/v1/health")
    assert "x-request-id" in response.headers
