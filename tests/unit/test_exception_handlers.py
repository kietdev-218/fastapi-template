"""
Unit tests for global exception handlers.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient
from starlette.exceptions import HTTPException as StarletteHTTPException

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
        raise AppException("Generic app error", code="CUSTOM_CODE", status_code=400)

    @app.get("/http-exception")
    async def raise_http_exception() -> None:
        raise StarletteHTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad input")

    @app.get("/generic-exception")
    async def raise_generic_exception() -> None:
        raise RuntimeError("Something went wrong")

    @app.post("/validation-error")
    async def raise_validation_error(data: dict) -> dict:
        return data

    return app


@pytest.mark.asyncio
async def test_not_found_handler(test_app: FastAPI) -> None:
    """NotFoundError must be handled and return HTTP 404."""
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        response = await ac.get("/not-found")
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "NOT_FOUND"
        assert data["error"]["message"] == "Resource missing"


@pytest.mark.asyncio
async def test_conflict_handler(test_app: FastAPI) -> None:
    """ConflictError must be handled and return HTTP 409."""
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        response = await ac.get("/conflict")
        assert response.status_code == 409
        data = response.json()
        assert data["error"]["code"] == "CONFLICT"
        assert data["error"]["message"] == "Resource exists"


@pytest.mark.asyncio
async def test_forbidden_handler(test_app: FastAPI) -> None:
    """ForbiddenError must be handled and return HTTP 403."""
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        response = await ac.get("/forbidden")
        assert response.status_code == 403
        data = response.json()
        assert data["error"]["code"] == "FORBIDDEN"
        assert data["error"]["message"] == "Access denied"


@pytest.mark.asyncio
async def test_unauthorised_handler(test_app: FastAPI) -> None:
    """UnauthorisedError must be handled and return HTTP 401."""
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        response = await ac.get("/unauthorised")
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "UNAUTHORISED"
        assert data["error"]["message"] == "Login required"


@pytest.mark.asyncio
async def test_app_exception_handler(test_app: FastAPI) -> None:
    """AppException must be handled and return defined status code and custom error code."""
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        response = await ac.get("/app-exception")
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "CUSTOM_CODE"
        assert data["error"]["message"] == "Generic app error"


@pytest.mark.asyncio
async def test_http_exception_handler(test_app: FastAPI) -> None:
    """StarletteHTTPException must be handled and return standard format."""
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        response = await ac.get("/http-exception")
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "BAD_REQUEST"
        assert data["error"]["message"] == "Bad input"


@pytest.mark.asyncio
async def test_generic_exception_handler(test_app: FastAPI) -> None:
    """Generic Exception must be handled and return HTTP 500."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app, raise_app_exceptions=False), base_url="http://test"
    ) as ac:
        response = await ac.get("/generic-exception")
        assert response.status_code == 500
        data = response.json()
        assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
        assert "unexpected error" in data["error"]["message"]


@pytest.mark.asyncio
async def test_validation_error_handler(test_app: FastAPI) -> None:
    """RequestValidationError must be handled and return HTTP 422."""
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        response = await ac.post("/validation-error", json="not a dictionary")
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "details" in data["error"]
