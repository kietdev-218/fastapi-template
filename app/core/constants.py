"""
Application constants and enums.
"""

from enum import IntEnum


class ApiCode(IntEnum):
    """
    Standardized API response codes.
    The code is a 5-digit integer structured as:
    [2-digit domain][1-digit HTTP group][2-digit sequence]
    """

    # General / System / Common Infrastructure (00)
    SUCCESS = 0
    CREATED = 1
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    TOO_MANY_REQUESTS = 429
    INTERNAL_SERVER_ERROR = 500
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503

    # Auth / Identity (10)
    TOKEN_EXPIRED = 10401
    TOKEN_INVALID = 10402

    # Authorization / Permission (15)
    PERMISSION_DENIED = 15403
    ROLE_INSIGNIFICANT = 15404
    RESOURCE_LOCKED = 15423
    SCOPE_MISSING = 15405

    # User (20)
    USER_NOT_FOUND = 20404
    USER_EMAIL_EXISTS = 20409

    # Order (30)
    ORDER_NOT_FOUND = 30404
    PRODUCT_OUT_OF_STOCK = 30422

    # Payment (40)
    INSUFFICIENT_BALANCE = 40422

    # Search (60)
    SEARCH_QUERY_ERROR = 60400
    INDEX_NOT_READY = 60503
    SEARCH_EMPTY_RESULTS = 60404

    # Integration / Third-party (70)
    PAYMENT_GATEWAY_ERROR = 70500
    THIRD_PARTY_TIMEOUT = 70504
    WEBHOOK_ERROR = 70400
    OAUTH_PROVIDER_FAILED = 70502

    # Validation / Input (80)
    VALIDATION_ERROR = 80400
    INVALID_FORMAT = 80401
    MISSING_REQUIRED_FIELDS = 80402
    DUPLICATE_DATA = 80409
