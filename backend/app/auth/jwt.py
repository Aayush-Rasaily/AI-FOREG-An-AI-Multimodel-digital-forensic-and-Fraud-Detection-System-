"""JWT access and refresh token helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import jwt

from backend.app.auth.exceptions import AuthenticationError


def encode_token(
    *,
    secret: str,
    algorithm: str,
    subject: UUID,
    session_id: UUID,
    token_type: str,
    expires_delta: timedelta,
    extra: dict[str, Any] | None = None,
) -> str:
    """Encode a signed JWT."""

    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "sid": str(session_id),
        "typ": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "jti": str(uuid4()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, secret, algorithm=algorithm)


def decode_token(*, token: str, secret: str, algorithm: str) -> dict[str, Any]:
    """Decode and validate a JWT, raising AuthenticationError on failure."""

    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=[algorithm],
            options={"require": ["exp", "iat", "sub", "sid", "typ"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationError("The access token has expired.") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthenticationError("The access token is invalid.") from exc
    if not isinstance(payload, dict):
        raise AuthenticationError("The access token is invalid.")
    return payload
