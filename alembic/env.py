"""
Alembic environment configuration.

Configures Alembic to run migrations against the application's
PostgreSQL database using an async-capable engine (asyncpg).

Two modes are supported:
- **Offline** (``--sql``): Generates a SQL script without connecting to the DB.
- **Online** (default): Connects to the DB and runs migrations directly.

The database URL is read from the application settings so that there is
a single source of truth for database configuration.
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# --------------------------------------------------------------------------- #
# Alembic Config object (provides access to alembic.ini values)
# --------------------------------------------------------------------------- #
config = context.config

# Set up Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --------------------------------------------------------------------------- #
# Application metadata for autogenerate
# --------------------------------------------------------------------------- #
# Import Base AFTER setting up logging to avoid circular imports
from app.core.settings import get_settings  # noqa: E402
from app.db.base import Base  # noqa: E402, F401 — all models imported here

settings = get_settings()

# Inject the database URL into Alembic config programmatically
# This overrides the (empty) sqlalchemy.url in alembic.ini
config.set_main_option("sqlalchemy.url", settings.async_database_url)

target_metadata = Base.metadata


# --------------------------------------------------------------------------- #
# Offline mode
# --------------------------------------------------------------------------- #


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    In offline mode, Alembic generates a SQL script that can be reviewed
    and applied manually — no live database connection is required.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# --------------------------------------------------------------------------- #
# Online mode (async)
# --------------------------------------------------------------------------- #


def do_run_migrations(connection: Connection) -> None:
    """Execute migrations synchronously within an async connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations in 'online' mode using an async SQLAlchemy engine.

    Creates an async engine from the Alembic config, obtains a sync
    connection (required by Alembic), and runs the migrations.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online migration mode."""
    asyncio.run(run_async_migrations())


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
