"""
Unit tests for base schemas, services, and db/API dependencies.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.api.v1.dependencies import DBSession
from app.db.base import Base as DbBase
from app.schemas.base import BaseSchema, TimestampSchema
from app.services.base import BaseService


def test_base_schema() -> None:
    """BaseSchema should parse valid data and support extra config attributes."""

    class UserSchema(BaseSchema):
        id: int
        name: str

    user = UserSchema(id=1, name=" John ")
    # Strips whitespace
    assert user.name == "John"


def test_timestamp_schema() -> None:
    """TimestampSchema should include created_at and updated_at fields."""
    now = datetime.now(UTC)
    schema = TimestampSchema(created_at=now, updated_at=now)
    assert schema.created_at == now
    assert schema.updated_at == now


@pytest.mark.asyncio
async def test_base_service() -> None:
    """BaseService abstract methods should raise NotImplementedError."""

    class DummyService(BaseService[dict, dict, dict]):
        pass

    service = DummyService()

    with pytest.raises(NotImplementedError):
        await service.get(1)

    with pytest.raises(NotImplementedError):
        await service.get_multi()

    with pytest.raises(NotImplementedError):
        await service.create({})

    with pytest.raises(NotImplementedError):
        await service.update(1, {})

    with pytest.raises(NotImplementedError):
        await service.delete(1)


def test_dependencies_and_db_base_imports() -> None:
    """Ensure dependencies and database base modules are importable."""
    assert DBSession is not None
    assert DbBase is not None
