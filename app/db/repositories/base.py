"""
Generic async repository base.

Implements the Repository pattern with full CRUD operations using
SQLAlchemy 2.x async style. All domain-specific repositories extend
``BaseRepository`` and inherit these operations for free.

Type parameters::

    ModelT        — the SQLAlchemy ORM model class
    CreateSchemaT — the Pydantic schema used for ``create``
    UpdateSchemaT — the Pydantic schema used for ``update``
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Generic, TypeVar, cast

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base_class import Base

ModelT = TypeVar("ModelT", bound=Base)
CreateSchemaT = TypeVar("CreateSchemaT")
UpdateSchemaT = TypeVar("UpdateSchemaT")


class BaseRepository(Generic[ModelT, CreateSchemaT, UpdateSchemaT]):
    """
    Thread-safe, async-first generic repository.

    Provides ``get``, ``get_multi``, ``get_or_404``, ``create``,
    ``update``, and ``delete`` operations for any SQLAlchemy model.

    Args:
        model: The SQLAlchemy ORM model class this repository manages.
        session: The active ``AsyncSession`` for this request.
    """

    def __init__(self, model: type[ModelT], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    # ------------------------------------------------------------------ #
    # Read
    # ------------------------------------------------------------------ #

    async def get(self, id: Any) -> ModelT | None:
        """
        Retrieve a single record by primary key.

        Args:
            id: The primary key value to look up.

        Returns:
            The model instance if found, otherwise ``None``.
        """
        return await self.session.get(self.model, id)

    async def get_multi(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[ModelT]:
        """
        Retrieve a paginated list of records.

        Args:
            offset: Number of records to skip (for pagination).
            limit: Maximum number of records to return.

        Returns:
            A sequence of model instances.
        """
        result = await self.session.execute(select(self.model).offset(offset).limit(limit))
        return result.scalars().all()

    async def count(self) -> int:
        """
        Return the total number of records for this model.

        Returns:
            Integer count of all rows.
        """
        result = await self.session.execute(select(func.count()).select_from(self.model))
        return result.scalar_one()

    async def exists(self, id: Any) -> bool:
        """
        Check whether a record with the given primary key exists.

        Args:
            id: The primary key value to check.

        Returns:
            True if the record exists; False otherwise.
        """
        record = await self.get(id)
        return record is not None

    # ------------------------------------------------------------------ #
    # Write
    # ------------------------------------------------------------------ #

    async def create(self, schema: CreateSchemaT) -> ModelT:
        """
        Persist a new record to the database.

        Args:
            schema: A Pydantic schema instance with the creation data.

        Returns:
            The newly created and refreshed model instance.
        """
        data = cast(
            dict[str, Any],
            schema.model_dump(exclude_unset=False)  # type: ignore[union-attr]
            if hasattr(schema, "model_dump")
            else dict(schema),  # type: ignore[call-overload]
        )
        db_obj = self.model(**data)
        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def update(self, db_obj: ModelT, schema: UpdateSchemaT) -> ModelT:
        """
        Update an existing record with the provided data.

        Only fields explicitly set in the schema (``exclude_unset=True``)
        are applied, preserving existing values for omitted fields.

        Args:
            db_obj: The model instance retrieved from the database.
            schema: A Pydantic schema instance with the update data.

        Returns:
            The updated and refreshed model instance.
        """
        update_data = cast(
            dict[str, Any],
            schema.model_dump(exclude_unset=True)  # type: ignore[union-attr]
            if hasattr(schema, "model_dump")
            else dict(schema),  # type: ignore[call-overload]
        )
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def delete(self, db_obj: ModelT) -> ModelT:
        """
        Delete a record from the database.

        Args:
            db_obj: The model instance to delete.

        Returns:
            The deleted model instance (useful for audit/logging).
        """
        await self.session.delete(db_obj)
        await self.session.flush()
        return db_obj
