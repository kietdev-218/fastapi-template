"""
Unit tests for security utilities.
"""

from __future__ import annotations

import jwt
import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.core.settings import get_settings


def test_password_hashing() -> None:
    """hash_password and verify_password must work correctly."""
    pwd = "secret-password"  # pragma: allowlist secret
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_jwt_tokens() -> None:
    """JWT token creation and decoding must work for HS256 algorithm."""
    settings = get_settings()
    # Temporarily set algorithm to HS256 for symmetric key test
    original_algorithm = settings.algorithm
    settings.algorithm = "HS256"

    try:
        subject = "user123"
        extra = {"role": "admin"}

        # Access token
        access_token = create_access_token(subject=subject, extra_claims=extra)
        decoded = decode_token(access_token)
        assert decoded["sub"] == subject
        assert decoded["role"] == "admin"
        assert "exp" in decoded

        # Refresh token
        refresh_token = create_refresh_token(subject=subject, extra_claims=extra)
        decoded_refresh = decode_token(refresh_token)
        assert decoded_refresh["sub"] == subject
        assert decoded_refresh["role"] == "admin"
        assert decoded_refresh["type"] == "refresh"
    finally:
        settings.algorithm = original_algorithm


def test_jwt_decode_errors() -> None:
    """Decoding invalid or expired tokens must raise PyJWTError."""
    with pytest.raises(jwt.PyJWTError):
        decode_token("invalid.token.string")
