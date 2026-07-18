"""
Abstract base service.

Defines the ``BaseService`` interface that all domain service classes must
implement. By inheriting from this abstract base, services remain consistent
and testable via dependency injection and mocking.

Design intent:
- Services contain *business logic* — they orchestrate repositories,
  apply domain rules, raise domain exceptions, and map data between layers.
- Services must NEVER contain raw SQL or direct ORM queries; those belong
  in repositories.
- Services are injected into API endpoints via FastAPI's ``Depends``.
"""

from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from typing import Any, Generic, TypeVar

ModelT = TypeVar("ModelT")
CreateSchemaT = TypeVar("CreateSchemaT")
UpdateSchemaT = TypeVar("UpdateSchemaT")
ResponseSchemaT = TypeVar("ResponseSchemaT")


class BaseService(ABC, Generic[ModelT, CreateSchemaT, UpdateSchemaT]):
    """
    Abstract base class for domain services.

    Subclasses should override the methods below and may add their own
    domain-specific methods.  The generic type parameters provide type
    safety at the call site without duplicating method signatures.

    Type Parameters:
        ModelT: The SQLAlchemy ORM model this service operates on.
        CreateSchemaT: Pydantic schema used for creation.
        UpdateSchemaT: Pydantic schema used for updates.
    """

    async def get(self, id: Any) -> ModelT | None:
        """Retrieve a single entity by primary key."""
        raise NotImplementedError

    async def get_multi(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[ModelT]:
        """Retrieve a paginated list of entities."""
        raise NotImplementedError

    async def create(self, schema: CreateSchemaT) -> ModelT:
        """Create and persist a new entity."""
        raise NotImplementedError

    async def update(self, id: Any, schema: UpdateSchemaT) -> ModelT:
        """Update an existing entity by primary key."""
        raise NotImplementedError

    async def delete(self, id: Any) -> ModelT:
        """Delete an entity by primary key."""
        raise NotImplementedError
