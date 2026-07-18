"""
Application lifecycle event handlers.

Centralises startup and shutdown logic (database engine initialisation,
connection pool warm-up, resource teardown, etc.) so that main.py remains
clean and all lifecycle concerns live in one place.

These handlers are wired into FastAPI via the ``lifespan`` context manager.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.settings import get_settings
from app.db.session import DatabaseSessionManager
from app.utils.logging import setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """
    FastAPI lifespan context manager.

    Handles startup and shutdown events in a single, clean async generator.
    Add any additional startup/shutdown logic here (Redis, Kafka consumers, etc.).

    Args:
        app: The FastAPI application instance.

    Yields:
        None — control is yielded to FastAPI while the application is running.
    """
    settings = get_settings()

    # ------------------------------------------------------------------ #
    # STARTUP
    # ------------------------------------------------------------------ #
    setup_logging(
        level=settings.log_level,
        log_format=settings.log_format,
        log_file=settings.log_file,
    )

    logger.info(
        "Starting %s v%s [%s]",
        settings.app_name,
        settings.app_version,
        settings.environment,
    )

    # Initialise the database connection pool
    DatabaseSessionManager.init(settings.async_database_url, settings=settings)
    logger.info("Database connection pool initialised")

    # Future startup hooks:
    # await redis_client.connect()
    # await kafka_producer.start()

    yield  # Application is running

    # ------------------------------------------------------------------ #
    # SHUTDOWN
    # ------------------------------------------------------------------ #
    logger.info("Shutting down %s …", settings.app_name)

    await DatabaseSessionManager.close()
    logger.info("Database connection pool closed")

    # Future shutdown hooks:
    # await redis_client.disconnect()
    # await kafka_producer.stop()

    logger.info("Shutdown complete")
