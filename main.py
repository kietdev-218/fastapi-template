"""
FastAPI application factory and entry point.

This module:
1. Creates the FastAPI application instance with full metadata.
2. Registers middleware (CORS, request logging).
3. Registers global exception handlers.
4. Mounts the versioned API router.
5. Provides the Uvicorn entry point when executed directly.

Design principle: ``main.py`` is intentionally thin — all configuration,
lifecycle management, and business logic is delegated to the appropriate
modules under ``app/``.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from app.api.v1.router import api_v1_router
from app.core.events import lifespan
from app.core.settings import get_settings
from app.core.telemetry import setup_telemetry
from app.middleware.exception_handlers import register_exception_handlers
from app.middleware.logging import RequestLoggingMiddleware
from app.utils.logging import setup_logging

settings = get_settings()

# Initialize logging early so all components (including Uvicorn startup/shutdown) use it
setup_logging(
    level=settings.log_level,
    log_format=settings.log_format,
    log_file=settings.log_file,
)


def create_application() -> FastAPI:
    """
    Application factory function.

    Creates and fully configures the FastAPI application instance.
    Using a factory allows easy creation of test-specific app instances
    with different configurations.

    Returns:
        A fully configured ``FastAPI`` application instance.
    """
    setup_telemetry()

    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        default_response_class=JSONResponse,
        lifespan=lifespan,
        contact={
            "name": "Platform Team",
            "email": "platform@example.com",
        },
        license_info={
            "name": "MIT",
        },
    )

    # ------------------------------------------------------------------ #
    # Middleware (registered in reverse order — last added = outermost)
    # ------------------------------------------------------------------ #

    # CORS — must be before request logging so pre-flight requests are handled
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # Request/Response logging with correlation IDs
    app.add_middleware(RequestLoggingMiddleware)

    # ------------------------------------------------------------------ #
    # Exception Handlers
    # ------------------------------------------------------------------ #
    register_exception_handlers(app)

    # ------------------------------------------------------------------ #
    # API Routers
    # ------------------------------------------------------------------ #
    app.include_router(api_v1_router, prefix=settings.api_v1_str)

    FastAPIInstrumentor.instrument_app(app)

    return app


# --------------------------------------------------------------------------- #
# Application instance — used by Uvicorn and test clients
# --------------------------------------------------------------------------- #
app: FastAPI = create_application()

# --------------------------------------------------------------------------- #
# Development server entry point
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        workers=settings.workers if not settings.reload else 1,
        log_config=None,
    )
