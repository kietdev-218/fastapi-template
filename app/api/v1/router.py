"""
API v1 router aggregator.

Combines all v1 endpoint routers into a single ``api_v1_router``
that is mounted on the FastAPI application in ``main.py``.

Adding a new resource:
1. Create ``app/api/v1/endpoints/<resource>.py``
2. Import its router here and call ``api_v1_router.include_router()``.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import health

api_v1_router = APIRouter()

# Health check (mounted at /api/v1/health)
api_v1_router.include_router(health.router)

# TODO: Add your resource routers here.
# Example:
#   from app.api.v1.endpoints import orders
#   api_v1_router.include_router(orders.router)
