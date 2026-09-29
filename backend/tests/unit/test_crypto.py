import pytest
from cryptography.fernet import InvalidToken

from app.core.crypto import decrypt_secret, encrypt_secret


def test_round_trip():
    assert decrypt_secret(encrypt_secret("sk-abc123")) == "sk-abc123"


def test_ciphertext_differs_from_plaintext():
    assert encrypt_secret("sk-abc123") != "sk-abc123"


def test_tampered_ciphertext_raises():
    with pytest.raises(InvalidToken):
        decrypt_secret("not-a-real-token")
