"""
FastAPI v1 API dependencies.

Provides reusable ``Depends`` callables that are shared across endpoint modules.

Currently included:
- Database session injection (``get_db``)

Extend this module as your service grows:
- Add repository/service providers when you add new resources.
- Add authentication dependencies when you implement auth.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

# --------------------------------------------------------------------------- #
# Type alias — use in endpoint signatures for clean DI
# --------------------------------------------------------------------------- #

DBSession = Annotated[AsyncSession, Depends(get_db)]

# TODO: Add service/repository dependencies here as you build out resources.
# Example:
#
#   from app.db.repositories.order_repo import OrderRepository
#   from app.services.order_service import OrderService
#
#   def get_order_repository(session: DBSession) -> OrderRepository:
#       return OrderRepository(session)
#
#   def get_order_service(
#       repo: Annotated[OrderRepository, Depends(get_order_repository)],
#   ) -> OrderService:
#       return OrderService(repo)
#
#   OrderServiceDep = Annotated[OrderService, Depends(get_order_service)]
