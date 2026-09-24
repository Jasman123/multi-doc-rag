"""Unit tests for password hashing and JWT encode/decode."""
from datetime import timedelta

import jwt
import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

# ── password hashing ────────────────────────────────────────────────────────────

def test_hash_password_returns_different_value_than_plaintext():
    assert hash_password("secret123") != "secret123"


def test_verify_password_roundtrip_succeeds():
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed) is True


def test_verify_password_wrong_password_fails():
    hashed = hash_password("secret123")
    assert verify_password("wrong-password", hashed) is False


def test_hash_password_is_salted():
    """Same input hashed twice should produce different hashes (random salt)."""
    assert hash_password("secret123") != hash_password("secret123")


# ── access token ─────────────────────────────────────────────────────────────

def test_access_token_decodes_with_expected_claims():
    token = create_access_token("user-id-1", "admin")
    payload = decode_token(token)
    assert payload["sub"] == "user-id-1"
    assert payload["role"] == "admin"
    assert payload["type"] == "access"


def test_access_token_expired_raises():
    token = create_access_token("user-id-1", "user", expires_delta=timedelta(seconds=-1))
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(token)


# ── refresh token ────────────────────────────────────────────────────────────

def test_refresh_token_decodes_with_expected_claims():
    token = create_refresh_token("user-id-1", token_version=3)
    payload = decode_token(token)
    assert payload["sub"] == "user-id-1"
    assert payload["ver"] == 3
    assert payload["type"] == "refresh"


def test_refresh_token_expired_raises():
    token = create_refresh_token("user-id-1", token_version=0, expires_delta=timedelta(seconds=-1))
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(token)


# ── tampering ──────────────────────────────────────────────────────────────────

def test_decode_token_rejects_bad_signature():
    token = create_access_token("user-id-1", "user")
    tampered = token[:-4] + "abcd"
    with pytest.raises(jwt.InvalidTokenError):
        decode_token(tampered)
