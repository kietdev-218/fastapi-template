"""
Security utilities module.

Provides JWT token creation/verification and password hashing/verification
using industry-standard libraries. Designed to be extended for OAuth2 or
API-key authentication flows.

Oathkeeper compatibility
------------------------
Tokens produced here include the required claims for Ory Oathkeeper's
``jwt`` authenticator:

- ``iss``  — matches ``trusted_issuers`` in the Oathkeeper rule config.
             Set via ``JWT_ISSUER`` env var.
- ``aud``  — matches ``target_audience`` in the Oathkeeper rule config.
             Set via ``JWT_AUDIENCE`` env var (comma-separated or JSON array).
- ``jti``  — cryptographically unique identifier required by the
             ``id_token`` mutator.
- ``sub``  — subject (user ID / identity ID from Kratos).
- ``exp``  — expiry timestamp (integer seconds since epoch as per RFC 7519).
- ``iat``  — issued-at timestamp.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import bcrypt
import jwt
from jwt import PyJWKClient

from app.core.settings import get_settings

# --------------------------------------------------------------------------- #
# Password Hashing
# --------------------------------------------------------------------------- #


def hash_password(plain_password: str) -> str:
    """
    Hash a plain-text password using bcrypt.

    Args:
        plain_password: The raw password string to hash.

    Returns:
        The bcrypt-hashed password string.
    """
    password_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a bcrypt hash.

    Args:
        plain_password: The raw password to verify.
        hashed_password: The stored bcrypt hash to compare against.

    Returns:
        True if the password matches; False otherwise.
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


# --------------------------------------------------------------------------- #
# JWT Tokens
# --------------------------------------------------------------------------- #

TokenData = dict[str, Any]


def _base_payload(subject: str | int, expire: datetime) -> TokenData:
    """
    Build the Oathkeeper-compatible JWT base payload.

    Includes the mandatory ``iss``, ``aud``, and ``jti`` claims so that
    the token passes Oathkeeper's ``jwt`` authenticator validation and is
    accepted by the ``id_token`` mutator pipeline.

    Args:
        subject: Token subject — typically the Kratos identity ID.
        expire: Absolute expiry ``datetime`` (must be timezone-aware UTC).

    Returns:
        A ``dict`` containing the standard JWT claims.
    """
    settings = get_settings()
    now = datetime.now(UTC)
    return {
        # RFC 7519 registered claims
        "iss": settings.jwt_issuer,  # Oathkeeper: trusted_issuers
        "sub": str(subject),
        "aud": settings.jwt_audience,  # Oathkeeper: target_audience (list)
        "exp": expire,
        "iat": now,
        "jti": str(uuid.uuid4()),  # Required by Oathkeeper id_token mutator
    }


def create_access_token(
    subject: str | int,
    extra_claims: TokenData | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a signed JWT access token.

    Args:
        subject: The token subject (typically a Kratos identity ID or email).
        extra_claims: Optional additional claims to embed in the token payload.
        expires_delta: Custom expiry duration; defaults to the configured value.

    Returns:
        A signed JWT string.
    """
    settings = get_settings()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    payload: TokenData = _base_payload(subject, expire)
    payload["type"] = "access"

    if extra_claims:
        # Guard: never allow overwriting the protected claims
        protected = {"iss", "sub", "aud", "exp", "iat", "jti"}
        payload.update({k: v for k, v in extra_claims.items() if k not in protected})

    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(
    subject: str | int,
    extra_claims: TokenData | None = None,
) -> str:
    """
    Create a signed JWT refresh token with a longer expiry.

    Args:
        subject: The token subject (typically a Kratos identity ID or email).
        extra_claims: Optional additional claims to embed in the token payload.

    Returns:
        A signed JWT string.
    """
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    payload: TokenData = _base_payload(subject, expire)
    payload["type"] = "refresh"

    if extra_claims:
        # Guard: never allow overwriting the protected claims
        protected = {"iss", "sub", "aud", "exp", "iat", "jti"}
        payload.update({k: v for k, v in extra_claims.items() if k not in protected})

    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


_jwk_client: PyJWKClient | None = None


def _get_jwk_client(jwks_url: str) -> PyJWKClient:
    global _jwk_client
    if _jwk_client is None:
        _jwk_client = PyJWKClient(jwks_url)
    return _jwk_client


def decode_token(token: str) -> TokenData:
    """
    Decode and verify a JWT token from Oathkeeper.

    Validates ``iss`` and ``aud`` against the configured values so that
    internally-decoded tokens undergo the same issuer/audience checks that
    Oathkeeper applies at the gateway.

    Args:
        token: The JWT string to decode.

    Returns:
        The decoded payload as a dictionary.

    Raises:
        PyJWTError: If the token is invalid, expired, has a bad signature,
                    or fails issuer/audience validation.
    """
    settings = get_settings()

    if settings.algorithm.startswith("RS"):
        jwk_client = _get_jwk_client(settings.jwks_url)
        signing_key = jwk_client.get_signing_key_from_jwt(token)
        key = signing_key.key
    else:
        key = settings.secret_key

    return cast(  # type: ignore[redundant-cast]
        TokenData,
        jwt.decode(
            token,
            key,
            algorithms=[settings.algorithm],
            audience=settings.jwt_audience,  # type: ignore[arg-type]
            issuer=settings.jwt_issuer,
        ),
    )
