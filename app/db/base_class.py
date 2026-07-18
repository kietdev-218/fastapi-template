"""
Declarative base class for all SQLAlchemy ORM models.

Provides a ``Base`` class with a standard set of columns (``id``,
``created_at``, ``updated_at``) via ``TimestampMixin``, reducing
repetition across every model in the project.
"""

from __future__ import annotations

import re
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


class TimestampMixin:
    """
    Mixin that adds ``created_at`` and ``updated_at`` audit columns.

    Both columns are timezone-aware and managed automatically by the
    database server, so application code never needs to set them manually.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        doc="Timestamp when this record was first created.",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp when this record was last updated.",
    )


class Base(DeclarativeBase):
    """
    SQLAlchemy declarative base for all ORM models.

    All models must inherit from this class.  Alembic's ``autogenerate``
    feature uses this base's metadata to detect schema changes.
    """

    # Automatically derive __tablename__ from class name (snake_case plural)
    # Individual models can override this attribute if needed.
    @declared_attr.directive
    def __tablename__(self) -> str:
        name = re.sub(r"(?<!^)(?=[A-Z])", "_", self.__name__).lower()
        if name.endswith("y"):
            return name[:-1] + "ies"
        elif name.endswith(("s", "x", "z", "ch", "sh")):
            return name + "es"
        else:
            return name + "s"
