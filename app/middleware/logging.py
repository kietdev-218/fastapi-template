"""
Request/Response logging middleware.

Attaches a unique ``X-Request-ID`` header to every request, logs
incoming requests and outgoing responses with timing information,
and propagates the request ID via Python's contextvars so that
structured log entries from anywhere in the call stack can include it.

This middleware is designed to be the outermost layer so that it captures
timing for the entire request lifecycle including other middleware.
"""

from __future__ import annotations

import logging
import time
from contextvars import ContextVar

from opentelemetry import trace
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.utils.helpers import generate_request_id

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Context variable — propagates request ID across async boundaries
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    """Return the current request's correlation ID, if available."""
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().trace_id, "032x")
    return request_id_var.get()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Starlette middleware that logs every HTTP request and response.

    Logs:
    - Method, path, and client IP on request arrival.
    - Status code and response time on request completion.
    - Attaches ``X-Request-ID`` header to every response.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        # Use X-Request-ID from client if provided, otherwise generate a new one
        request_id = request.headers.get("X-Request-ID") or generate_request_id()
        token = request_id_var.set(request_id)

        start_time = time.perf_counter()

        logger.info(
            "Request: %s %s",
            request.method,
            request.url.path,
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else "unknown",
                "query_params": str(request.query_params),
            },
        )

        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000

            logger.info(
                "Response: %s %s %d (%.2fms)",
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                },
            )

            response.headers["X-Request-ID"] = request_id
            return response
        except Exception:
            logger.exception(
                "Unhandled exception during %s %s",
                request.method,
                request.url.path,
                extra={"request_id": request_id},
            )
            raise
        finally:
            request_id_var.reset(token)
