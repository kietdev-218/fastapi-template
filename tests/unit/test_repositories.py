"""
Unit tests for the generic database repository.
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base
from app.db.repositories.base import BaseRepository


class DummyModel(Base):
    __tablename__ = "dummy_model"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(nullable=False)


class DummyCreate(BaseModel):
    name: str


class DummyUpdate(BaseModel):
    name: str


@pytest.mark.asyncio
async def test_base_repository_crud(db_session: AsyncSession) -> None:
    """BaseRepository must support standard CRUD lifecycle."""
    # Register/create the dummy model table in the isolated SQLite memory DB
    async with db_session.bind.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # type: ignore[union-attr]

    repo = BaseRepository[DummyModel, DummyCreate, DummyUpdate](DummyModel, db_session)

    # 1. Verify initially empty
    assert await repo.count() == 0
    assert await repo.exists(1) is False
    assert await repo.get(1) is None
    assert len(await repo.get_multi()) == 0

    # 2. Create record
    created = await repo.create(DummyCreate(name="Item 1"))
    assert created.id is not None
    assert created.name == "Item 1"

    # 3. Read record
    assert await repo.count() == 1
    assert await repo.exists(created.id) is True

    fetched = await repo.get(created.id)
    assert fetched is not None
    assert fetched.name == "Item 1"

    # 4. Get multi
    multi = await repo.get_multi(offset=0, limit=10)
    assert len(multi) == 1
    assert multi[0].name == "Item 1"

    # 5. Update record
    updated = await repo.update(created, DummyUpdate(name="Updated Item"))
    assert updated.name == "Updated Item"

    # Verify updated record in DB
    refetched = await repo.get(created.id)
    assert refetched is not None
    assert refetched.name == "Updated Item"

    # 6. Delete record
    deleted = await repo.delete(updated)
    assert deleted.id == created.id
    assert await repo.count() == 0
