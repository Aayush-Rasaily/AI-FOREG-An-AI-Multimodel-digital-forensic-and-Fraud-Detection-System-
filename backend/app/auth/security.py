"""Password policy, lockout, and request identity helpers."""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import UTC, datetime, timedelta

from fastapi import Request

from backend.app.auth.exceptions import AuthenticationError, PasswordPolicyError
from backend.app.auth.policy import (
    IP_MAX_FAILURES,
    IP_WINDOW_MINUTES,
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    USERNAME_MAX_LENGTH,
    USERNAME_MIN_LENGTH,
)

_USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")
_ip_failures: dict[str, list[datetime]] = defaultdict(list)


def validate_username(username: str) -> str:
    """Normalize and validate a username."""

    value = username.strip()
    if (
        len(value) < USERNAME_MIN_LENGTH
        or len(value) > USERNAME_MAX_LENGTH
        or _USERNAME_PATTERN.fullmatch(value) is None
    ):
        raise PasswordPolicyError(
            "Usernames must be 3-64 characters and use letters, digits, or underscores."
        )
    return value


def validate_password(password: str) -> None:
    """Enforce the platform password policy."""

    if len(password) < PASSWORD_MIN_LENGTH or len(password) > PASSWORD_MAX_LENGTH:
        raise PasswordPolicyError(
            "Passwords must be between 12 and 128 characters."
        )
    classes = [
        any(char.islower() for char in password),
        any(char.isupper() for char in password),
        any(char.isdigit() for char in password),
        any(not char.isalnum() for char in password),
    ]
    if not all(classes):
        raise PasswordPolicyError(
            "Passwords must include uppercase, lowercase, digit, "
            "and special characters."
        )


def client_ip(request: Request) -> str | None:
    """Return the connecting client address when available."""

    if request.client is None:
        return None
    return request.client.host


def parse_user_agent(user_agent: str | None) -> tuple[str | None, str | None]:
    """Return a coarse browser and device label from a user-agent string."""

    if not user_agent:
        return None, None
    browser = "Unknown"
    lowered = user_agent.lower()
    if "edg/" in lowered:
        browser = "Edge"
    elif "chrome/" in lowered and "chromium" not in lowered:
        browser = "Chrome"
    elif "firefox/" in lowered:
        browser = "Firefox"
    elif "safari/" in lowered:
        browser = "Safari"
    device = "Desktop"
    if "mobile" in lowered or "android" in lowered or "iphone" in lowered:
        device = "Mobile"
    return browser, device


def register_ip_failure(ip_address: str | None) -> None:
    """Record a failed login for throttling."""

    if not ip_address:
        return
    now = datetime.now(UTC)
    cutoff = now - timedelta(minutes=IP_WINDOW_MINUTES)
    recent = [stamp for stamp in _ip_failures[ip_address] if stamp >= cutoff]
    recent.append(now)
    _ip_failures[ip_address] = recent


def assert_ip_allowed(ip_address: str | None) -> None:
    """Reject requests from addresses that exceeded the failure window."""

    if not ip_address:
        return
    now = datetime.now(UTC)
    cutoff = now - timedelta(minutes=IP_WINDOW_MINUTES)
    recent = [stamp for stamp in _ip_failures[ip_address] if stamp >= cutoff]
    _ip_failures[ip_address] = recent
    if len(recent) >= IP_MAX_FAILURES:
        raise AuthenticationError(
            "Too many failed sign-in attempts. Try again later."
        )


def clear_ip_failures(ip_address: str | None) -> None:
    """Clear throttling state after a successful login."""

    if ip_address and ip_address in _ip_failures:
        del _ip_failures[ip_address]


def extract_bearer_token(request: Request) -> str | None:
    """Read a Bearer token from the Authorization header."""

    header = request.headers.get("Authorization")
    if header is None:
        return None
    scheme, _, value = header.partition(" ")
    if scheme.lower() != "bearer" or not value.strip():
        return None
    return value.strip()
