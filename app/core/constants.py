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

    # General / System (00)
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

    VALIDATION_ERROR = 40000

    # Auth (10)
    TOKEN_EXPIRED = 10401
    TOKEN_INVALID = 10402

    # User (20)
    USER_NOT_FOUND = 20404
    USER_EMAIL_EXISTS = 20409

    # Order (30)
    ORDER_NOT_FOUND = 30404
    PRODUCT_OUT_OF_STOCK = 30422

    # Payment (40)
    INSUFFICIENT_BALANCE = 40422
    PAYMENT_GATEWAY_ERROR = 40500
