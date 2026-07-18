"""
Model aggregation for Alembic autogenerate.

This module imports every ORM model so that Alembic's ``autogenerate``
feature can detect the complete schema and generate accurate migrations.

**Important**: Keep this module up-to-date whenever a new model is added.

Usage in alembic/env.py::

    from app.db.base import Base  # noqa: F401 — imports all models
    target_metadata = Base.metadata
"""

from app.db.base_class import Base  # noqa: F401

# TODO: Import your models here so Alembic can detect them.
# Example:
#   from app.models.order import Order  # noqa: F401

__all__ = ["Base"]
