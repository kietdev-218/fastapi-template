"""
Global exception handlers.

Registers FastAPI/Starlette exception handlers that convert exceptions into
consistent, structured JSON error responses. All error responses follow the
same envelope shape so that clients can handle them uniformly.

Error response shape::

    {
        "error": {
            "code": "NOT_FOUND",
            "message": "User with id=42 not found.",
            "details": null,
            "request_id": "abc123"
        }
    }
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

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
        code: Machine-readable error code string.
        status_code: HTTP status code for the response.
        details: Optional structured details (dict or list).
    """

    def __init__(
        self,
        message: str,
        *,
        code: str = "APPLICATION_ERROR",
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
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class ConflictError(AppException):
    """Raised when a uniqueness constraint is violated."""

    def __init__(self, message: str = "Resource already exists.", details: Any = None) -> None:
        super().__init__(
            message,
            code="CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class ForbiddenError(AppException):
    """Raised when the caller lacks permission to perform an action."""

    def __init__(self, message: str = "Permission denied.", details: Any = None) -> None:
        super().__init__(
            message,
            code="FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class UnauthorisedError(AppException):
    """Raised when the caller is not authenticated."""

    def __init__(self, message: str = "Authentication required.", details: Any = None) -> None:
        super().__init__(
            message,
            code="UNAUTHORISED",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


# --------------------------------------------------------------------------- #
# Response builder
# --------------------------------------------------------------------------- #


def _error_response(
    status_code: int,
    code: str,
    message: str,
    details: Any = None,
    request: Request | None = None,
) -> JSONResponse:
    """Build a standardised JSON error response."""
    from app.middleware.logging import get_request_id

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details,
                "request_id": get_request_id() if request else None,
            }
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
        return _error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code="VALIDATION_ERROR",
            message="Request validation failed. Please check the provided data.",
            details=exc.errors(),
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
            details=exc.details,
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
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred. Please try again later.",
            request=request,
        )


def _status_to_code(status_code: int) -> str:
    """Map common HTTP status codes to machine-readable error codes."""
    _mapping: dict[int, str] = {
        400: "BAD_REQUEST",
        401: "UNAUTHORISED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
    }
    return _mapping.get(status_code, "HTTP_ERROR")
