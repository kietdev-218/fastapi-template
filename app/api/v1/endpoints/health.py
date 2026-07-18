"""
Health check and system status endpoints.

Provides a standardized ``GET /health`` endpoint that returns the current
service status, version, environment, and statuses of backend dependencies
such as the PostgreSQL database and Redis cache, wrapped in the standard
API response envelope. Conforms to the draft IETF specification for API Health Checks.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime

from fastapi import APIRouter, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text

from app.api.v1.dependencies import DBSession, RedisDep
from app.core.constants import ApiCode
from app.core.settings import get_settings
from app.middleware.logging import get_request_id
from app.schemas.responses.api import ApiResponse

router = APIRouter(tags=["Health"])


class HealthJSONResponse(JSONResponse):
    """Custom response class to set the application/health+json media type."""

    media_type = "application/health+json"


class HealthCheckDetails(BaseModel):
    """Detailed health check result for a component."""

    component_id: str | None = Field(
        default=None,
        validation_alias="componentId",
        serialization_alias="componentId",
        description="Unique identifier for the component",
    )
    component_type: str = Field(
        ...,
        validation_alias="componentType",
        serialization_alias="componentType",
        description="Type of the component (e.g. datastore, cache)",
    )
    status: str = Field(..., description="Health status of the component: pass, warn, fail")
    time: str = Field(..., description="Timestamp when the check was performed")
    latency_ms: float | None = Field(
        default=None,
        validation_alias="latencyMs",
        serialization_alias="latencyMs",
        description="Latency of the health check query in milliseconds",
    )
    output: str | None = Field(default=None, description="Error message or extra context if the check failed")

    model_config = ConfigDict(populate_by_name=True)


class HealthResponse(BaseModel):
    """Standardized IETF Draft health check response schema."""

    status: str = Field(..., description="Overall status of the service: pass, warn, fail")
    version: str = Field(..., description="Public version of the service")
    release_id: str = Field(
        ...,
        validation_alias="releaseId",
        serialization_alias="releaseId",
        description="Internal version or release identifier",
    )
    notes: list[str] = Field(default_factory=list, description="Array of non-structured notes")
    checks: dict[str, list[HealthCheckDetails]] = Field(
        default_factory=dict, description="Map of detail objects for each component checked"
    )

    model_config = ConfigDict(populate_by_name=True)


@router.get(
    "/health",
    response_model=ApiResponse[HealthResponse],
    response_class=HealthJSONResponse,
    summary="Health Check",
    description=(
        "Returns the standardized health status of the service and its dependencies "
        "(database, redis). Intended for use by load balancers and orchestrators."
    ),
    responses={
        200: {
            "description": "Service and all dependencies are healthy",
            "content": {
                "application/health+json": {
                    "example": {
                        "success": True,
                        "code": 0,
                        "message": "Service is healthy",
                        "data": {
                            "status": "pass",
                            "version": "1.0.0",
                            "releaseId": "1.0.0",
                            "notes": ["Environment: development"],
                            "checks": {
                                "database:connection": [
                                    {
                                        "componentId": "postgres",
                                        "componentType": "datastore",
                                        "status": "pass",
                                        "time": "2026-07-17T21:00:00+00:00",
                                        "latencyMs": 1.25,
                                        "output": None,
                                    }
                                ],
                                "redis:connection": [
                                    {
                                        "componentId": "redis",
                                        "componentType": "cache",
                                        "status": "pass",
                                        "time": "2026-07-17T21:00:00+00:00",
                                        "latencyMs": 0.45,
                                        "output": None,
                                    }
                                ],
                            },
                        },
                        "meta": None,
                        "errors": None,
                        "timestamp": "2026-07-18T10:00:00Z",
                        "traceId": "req-8f2e1a",
                    }
                }
            },
        },
        503: {
            "description": "One or more dependencies are unhealthy",
            "content": {
                "application/health+json": {
                    "example": {
                        "success": False,
                        "code": 503,
                        "message": "Service is unhealthy",
                        "data": {
                            "status": "fail",
                            "version": "1.0.0",
                            "releaseId": "1.0.0",
                            "notes": ["Environment: development"],
                            "checks": {
                                "database:connection": [
                                    {
                                        "componentId": "postgres",
                                        "componentType": "datastore",
                                        "status": "fail",
                                        "time": "2026-07-17T21:00:00+00:00",
                                        "latencyMs": 2.10,
                                        "output": "Connection refused",
                                    }
                                ],
                                "redis:connection": [
                                    {
                                        "componentId": "redis",
                                        "componentType": "cache",
                                        "status": "pass",
                                        "time": "2026-07-17T21:00:00+00:00",
                                        "latencyMs": 0.45,
                                        "output": None,
                                    }
                                ],
                            },
                        },
                        "meta": None,
                        "errors": None,
                        "timestamp": "2026-07-18T10:00:00Z",
                        "traceId": "req-8f2e1a",
                    }
                }
            },
        },
    },
)
async def health_check(
    response: Response,
    db: DBSession,
    redis: RedisDep,
) -> ApiResponse[HealthResponse]:
    """
    Service health check endpoint.

    Checks connections to the database and Redis cache, computes execution latency,
    and returns a standardized response.
    """
    settings = get_settings()

    # 1. Database Check
    db_start = time.perf_counter()
    db_status = "pass"
    db_output = None
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = "fail"
        db_output = str(e)
    db_latency = (time.perf_counter() - db_start) * 1000

    # 2. Redis Check
    redis_start = time.perf_counter()
    redis_status = "pass"
    redis_output = None
    try:
        await redis.ping()
    except Exception as e:
        redis_status = "fail"
        redis_output = str(e)
    redis_latency = (time.perf_counter() - redis_start) * 1000

    # 3. Overall Status Decision
    overall_status = "pass"
    is_success = True
    api_code = 0
    api_message = "Service is healthy"

    if db_status == "fail" or redis_status == "fail":
        overall_status = "fail"
        is_success = False
        api_code = ApiCode.SERVICE_UNAVAILABLE
        api_message = "Service is unhealthy"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    now = datetime.now(UTC).isoformat(timespec="seconds")
    if now.endswith("+00:00"):
        now = now[:-6] + "Z"

    return ApiResponse[HealthResponse](
        success=is_success,
        code=api_code,
        message=api_message,
        data=HealthResponse(
            status=overall_status,
            version=settings.app_version,
            release_id=settings.app_version,
            notes=[f"Environment: {settings.environment}"],
            checks={
                "database:connection": [
                    HealthCheckDetails(
                        component_id="postgres",
                        component_type="datastore",
                        status=db_status,
                        time=datetime.now(UTC).isoformat(),
                        latency_ms=round(db_latency, 2),
                        output=db_output,
                    )
                ],
                "redis:connection": [
                    HealthCheckDetails(
                        component_id="redis",
                        component_type="cache",
                        status=redis_status,
                        time=datetime.now(UTC).isoformat(),
                        latency_ms=round(redis_latency, 2),
                        output=redis_output,
                    )
                ],
            },
        ),
        meta=None,
        errors=None,
        timestamp=now,
        trace_id=get_request_id() or "unknown",
    )
