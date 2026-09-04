"""Regression tests for JWT authentication helpers."""

from datetime import timedelta

import jwt
import pytest

from app.auth import create_access_token, settings

TEST_SECRET = "test-only-signing-key-with-at-least-32-bytes"


def test_access_token_contains_subject(monkeypatch: pytest.MonkeyPatch) -> None:
    """Created access tokens can be verified with the configured key."""
    monkeypatch.setattr(settings, "secret_key", TEST_SECRET)
    token = create_access_token({"sub": "test-user"}, timedelta(minutes=5))

    payload = jwt.decode(
        token,
        TEST_SECRET,
        algorithms=[settings.algorithm],
    )

    assert payload["sub"] == "test-user"
    assert "exp" in payload


def test_access_token_rejects_wrong_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tokens cannot be verified with a different signing key."""
    monkeypatch.setattr(settings, "secret_key", TEST_SECRET)
    token = create_access_token({"sub": "test-user"}, timedelta(minutes=5))

    with pytest.raises(jwt.InvalidSignatureError):
        jwt.decode(
            token,
            "different-test-only-signing-key-over-32-bytes",
            algorithms=[settings.algorithm],
        )
