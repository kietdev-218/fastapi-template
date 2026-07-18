"""
Standardized generic API response schemas.
"""

from typing import Any, Generic, TypeVar

from pydantic import Field

from app.schemas.base import BaseSchema

T = TypeVar("T")


class PaginationMeta(BaseSchema):
    """Pagination metadata for list responses."""

    page: int
    page_size: int = Field(alias="pageSize")
    total_items: int = Field(alias="totalItems")
    total_pages: int = Field(alias="totalPages")
    has_next: bool = Field(alias="hasNext")
    has_prev: bool = Field(alias="hasPrev")


class ErrorDetail(BaseSchema):
    """Detailed validation error for a specific field."""

    field: str
    message: str


class ApiResponse(BaseSchema, Generic[T]):
    """
    Standard API Response envelope.
    All endpoints should return data wrapped in this envelope.
    """

    success: bool
    code: int
    message: str
    data: T | None = None
    meta: Any = None
    errors: list[ErrorDetail] | None = None
    timestamp: str
    trace_id: str = Field(validation_alias="traceId", serialization_alias="traceId")


class PaginatedApiResponse(ApiResponse[list[T]]):
    """
    Standard API Response envelope for paginated lists.
    The `data` field will be a list of `T` and `meta` will contain pagination details.
    """

    class _Meta(BaseSchema):
        pagination: PaginationMeta

    meta: _Meta  # type: ignore[reportGeneralTypeIssues]
