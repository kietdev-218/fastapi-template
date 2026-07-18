"""
Unit tests for global exception handlers.
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.constants import ApiCode
from app.middleware.exception_handlers import (
    AppException,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorisedError,
    register_exception_handlers,
)


@pytest.fixture
def test_app() -> FastAPI:
    """Create a test FastAPI application with registered exception handlers."""
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/not-found")
    async def raise_not_found() -> None:
        raise NotFoundError("Resource missing")

    @app.get("/conflict")
    async def raise_conflict() -> None:
        raise ConflictError("Resource exists")

    @app.get("/forbidden")
    async def raise_forbidden() -> None:
        raise ForbiddenError("Access denied")

    @app.get("/unauthorised")
    async def raise_unauthorised() -> None:
        raise UnauthorisedError("Login required")

    @app.get("/app-exception")
    async def raise_app_exception() -> None:
        raise AppException("Generic app error", code=99999, status_code=400)

    @app.get("/http-exception")
    async def raise_http_exception() -> None:
        raise StarletteHTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad input")

    @app.get("/generic-exception")
    async def raise_generic_exception() -> None:
        raise RuntimeError("Something went wrong")

    @app.post("/validation-error")
    async def raise_validation_error(data: dict[str, Any]) -> dict[str, Any]:
        return data

    return app


@pytest.mark.asyncio
async def test_not_found_handler(test_app: FastAPI) -> None:
    """NotFoundError must be handled and return HTTP 404."""
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        response = await ac.get("/not-found")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["code"] == ApiCode.NOT_FOUND
        assert data["message"] == "Resource missing"
        assert data["errors"] is None
        assert "timestamp" in data
        assert "traceId" in data


@pytest.mark.asyncio
async def test_conflict_handler(test_app: FastAPI) -> None:
    """ConflictError must be handled and return HTTP 409."""
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        response = await ac.get("/conflict")
        assert response.status_code == 409
        data = response.json()
        assert data["success"] is False
        assert data["code"] == ApiCode.CONFLICT
        assert data["message"] == "Resource exists"
        assert data["errors"] is None
        assert "timestamp" in data
        assert "traceId" in data


@pytest.mark.asyncio
async def test_forbidden_handler(test_app: FastAPI) -> None:
    """ForbiddenError must be handled and return HTTP 403."""
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        response = await ac.get("/forbidden")
        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert data["code"] == ApiCode.FORBIDDEN
        assert data["message"] == "Access denied"
        assert data["errors"] is None
        assert "timestamp" in data
        assert "traceId" in data


@pytest.mark.asyncio
async def test_unauthorised_handler(test_app: FastAPI) -> None:
    """UnauthorisedError must be handled and return HTTP 401."""
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        response = await ac.get("/unauthorised")
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["code"] == ApiCode.UNAUTHORIZED
        assert data["message"] == "Login required"
        assert data["errors"] is None
        assert "timestamp" in data
        assert "traceId" in data


@pytest.mark.asyncio
async def test_app_exception_handler(test_app: FastAPI) -> None:
    """AppException must be handled and return defined status code and custom error code."""
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        response = await ac.get("/app-exception")
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["code"] == 99999
        assert data["message"] == "Generic app error"
        assert data["errors"] is None
        assert "timestamp" in data
        assert "traceId" in data


@pytest.mark.asyncio
async def test_http_exception_handler(test_app: FastAPI) -> None:
    """StarletteHTTPException must be handled and return standard format."""
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        response = await ac.get("/http-exception")
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["code"] == ApiCode.BAD_REQUEST
        assert data["message"] == "Bad input"
        assert data["errors"] is None
        assert "timestamp" in data
        assert "traceId" in data


@pytest.mark.asyncio
async def test_generic_exception_handler(test_app: FastAPI) -> None:
    """Generic Exception must be handled and return HTTP 500."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app, raise_app_exceptions=False), base_url="http://test"
    ) as ac:
        response = await ac.get("/generic-exception")
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert data["code"] == ApiCode.INTERNAL_SERVER_ERROR
        assert "unexpected error" in data["message"]
        assert data["errors"] is None
        assert "timestamp" in data
        assert "traceId" in data


@pytest.mark.asyncio
async def test_validation_error_handler(test_app: FastAPI) -> None:
    """RequestValidationError must be handled and return HTTP 422."""
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        response = await ac.post("/validation-error", json="not a dictionary")
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert data["code"] == ApiCode.VALIDATION_ERROR
        assert "errors" in data
        assert len(data["errors"]) > 0
        assert "field" in data["errors"][0]
        assert "message" in data["errors"][0]
        assert "timestamp" in data
        assert "traceId" in data
