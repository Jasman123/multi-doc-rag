"""REGISTRATION_CODE parsing: blank/whitespace must mean "open", not "match an empty code"."""
import pytest

from app.core.config import Settings

_BASE = {
    "database_url": "postgresql+asyncpg://u:p@localhost/db",
    "secret_key": "s",
    "encryption_key": "k",
}


def _settings(**overrides) -> Settings:
    # _env_file=None: ignore any developer backend/.env so only the given values count.
    return Settings(_env_file=None, **_BASE, **overrides)


def test_registration_code_defaults_to_none():
    assert _settings().registration_code is None


@pytest.mark.parametrize("raw", ["", "   ", "\n\t"])
def test_blank_registration_code_means_open(raw):
    assert _settings(registration_code=raw).registration_code is None


def test_registration_code_is_stripped():
    assert _settings(registration_code="  invite-123 \n").registration_code == "invite-123"
