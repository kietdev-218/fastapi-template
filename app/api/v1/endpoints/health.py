"""
Health check and system status endpoints.

Provides a simple ``GET /health`` endpoint that returns the current
service status, version, and environment. Used by load balancers,
orchestrators (Kubernetes liveness/readiness probes), and monitoring tools.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.settings import get_settings

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str
    service: str
    version: str
    timestamp: str
    environment: str


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description=(
        "Returns the current health status of the service. Intended for use by load balancers and orchestrators."
    ),
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "service": "FastAPI Microservice",
                        "version": "1.0.0",
                        "timestamp": "2026-07-17T21:00:00+00:00",
                        "environment": "development",
                    }
                }
            },
        }
    },
)
async def health_check() -> HealthResponse:
    """
    Service health check endpoint.

    Returns:
        A ``HealthResponse`` indicating the service is up and operational.
    """
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,
        timestamp=datetime.now(UTC).isoformat(),
        environment=settings.environment,
    )
