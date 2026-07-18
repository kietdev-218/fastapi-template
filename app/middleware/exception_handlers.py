"""
Global exception handlers.

Registers FastAPI/Starlette exception handlers that convert exceptions into
consistent, structured JSON error responses. All error responses follow the
same envelope shape so that clients can handle them uniformly.

Error response shape::

    {
        "success": false,
        "code": 40000,
        "message": "Validation error",
        "data": null,
        "meta": null,
        "errors": [{"field": "email", "message": "Invalid format"}],
        "timestamp": "2026-07-18T10:00:00Z",
        "traceId": "abc123"
    }
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.constants import ApiCode

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Domain exception hierarchy
# --------------------------------------------------------------------------- #


class AppException(Exception):
    """
    Base class for all application-level domain exceptions.

    Raise subclasses of this from service/repository layers.
    The exception handler below converts them to HTTP responses automatically.

    Args:
        message: Human-readable error description.
        code: Machine-readable integer error code.
        status_code: HTTP status code for the response.
        details: Optional structured details for the `errors` array.
    """

    def __init__(
        self,
        message: str,
        *,
        code: int = ApiCode.INTERNAL_SERVER_ERROR,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


class NotFoundError(AppException):
    """Raised when a requested resource does not exist."""

    def __init__(self, message: str = "Resource not found.", details: Any = None) -> None:
        super().__init__(
            message,
            code=ApiCode.NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class ConflictError(AppException):
    """Raised when a uniqueness constraint is violated."""

    def __init__(self, message: str = "Resource already exists.", details: Any = None) -> None:
        super().__init__(
            message,
            code=ApiCode.CONFLICT,
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class ForbiddenError(AppException):
    """Raised when the caller lacks permission to perform an action."""

    def __init__(self, message: str = "Permission denied.", details: Any = None) -> None:
        super().__init__(
            message,
            code=ApiCode.FORBIDDEN,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class UnauthorisedError(AppException):
    """Raised when the caller is not authenticated."""

    def __init__(self, message: str = "Authentication required.", details: Any = None) -> None:
        super().__init__(
            message,
            code=ApiCode.UNAUTHORIZED,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


# --------------------------------------------------------------------------- #
# Response builder
# --------------------------------------------------------------------------- #


def _error_response(
    status_code: int,
    code: int,
    message: str,
    errors: Any = None,
    request: Request | None = None,
) -> JSONResponse:
    """Build a standardised JSON error response envelope."""
    from app.middleware.logging import get_request_id

    now = datetime.now(UTC).isoformat(timespec="seconds")
    trace_id = get_request_id() if request else None

    # Force format Z for UTC if it has +00:00
    if now.endswith("+00:00"):
        now = now[:-6] + "Z"

    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "code": code,
            "message": message,
            "data": None,
            "meta": None,
            "errors": errors,
            "timestamp": now,
            "traceId": trace_id or "unknown",
        },
    )


# --------------------------------------------------------------------------- #
# Handler registration
# --------------------------------------------------------------------------- #


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all global exception handlers on the FastAPI application.

    Args:
        app: The FastAPI application instance.
    """

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        """Handle FastAPI/Starlette HTTP exceptions."""
        logger.warning(
            "HTTP %d: %s — %s %s",
            exc.status_code,
            exc.detail,
            request.method,
            request.url.path,
        )
        return _error_response(
            status_code=exc.status_code,
            code=_status_to_code(exc.status_code),
            message=str(exc.detail),
            request=request,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """Handle Pydantic request validation errors (422 Unprocessable Entity)."""
        logger.warning(
            "Validation error on %s %s: %s",
            request.method,
            request.url.path,
            exc.errors(),
        )
        # Format Pydantic errors to our standard {"field": "...", "message": "..."}
        formatted_errors = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error.get("loc", []))
            formatted_errors.append({"field": field, "message": error.get("msg")})

        return _error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code=ApiCode.VALIDATION_ERROR,
            message="Request validation failed. Please check the provided data.",
            errors=formatted_errors,
            request=request,
        )

    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request,
        exc: AppException,
    ) -> JSONResponse:
        """Handle domain-level application exceptions."""
        logger.warning(
            "AppException [%s]: %s — %s %s",
            exc.code,
            exc.message,
            request.method,
            request.url.path,
        )
        return _error_response(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            errors=exc.details,
            request=request,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Catch-all handler for unexpected exceptions."""
        logger.exception(
            "Unhandled exception on %s %s",
            request.method,
            request.url.path,
        )
        return _error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code=ApiCode.INTERNAL_SERVER_ERROR,
            message="An unexpected error occurred. Please try again later.",
            request=request,
        )


def _status_to_code(status_code: int) -> int:
    """Map common HTTP status codes to machine-readable error codes."""
    _mapping: dict[int, int] = {
        400: ApiCode.BAD_REQUEST,
        401: ApiCode.UNAUTHORIZED,
        403: ApiCode.FORBIDDEN,
        404: ApiCode.NOT_FOUND,
        405: ApiCode.METHOD_NOT_ALLOWED,
        409: ApiCode.CONFLICT,
        422: ApiCode.UNPROCESSABLE_ENTITY,
        429: ApiCode.TOO_MANY_REQUESTS,
        500: ApiCode.INTERNAL_SERVER_ERROR,
        502: ApiCode.BAD_GATEWAY,
        503: ApiCode.SERVICE_UNAVAILABLE,
    }
    return _mapping.get(status_code, ApiCode.INTERNAL_SERVER_ERROR)
