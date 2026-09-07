"""HTTP security header builders (Phase 10D)."""

from __future__ import annotations

from typing import Any

from backend.app.security.csp import api_content_security_policy


def build_security_headers(
    *,
    enable_hsts: bool = False,
    hsts_max_age: int = 31536000,
    csp: str | None = None,
) -> dict[str, str]:
    """Return enterprise security headers for API responses."""

    headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "no-referrer",
        "Permissions-Policy": (
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
            "magnetometer=(), microphone=(), payment=(), usb=()"
        ),
        "Cross-Origin-Resource-Policy": "same-origin",
        "Cross-Origin-Opener-Policy": "same-origin",
        "Cross-Origin-Embedder-Policy": "require-corp",
        "Content-Security-Policy": csp or api_content_security_policy(),
        "X-Permitted-Cross-Domain-Policies": "none",
        "Cache-Control": "no-store",
    }
    if enable_hsts:
        headers["Strict-Transport-Security"] = (
            f"max-age={max(0, hsts_max_age)}; includeSubDomains; preload"
        )
    return headers


def apply_security_headers(
    response_headers: Any,
    *,
    enable_hsts: bool = False,
    hsts_max_age: int = 31536000,
    csp: str | None = None,
) -> None:
    """Apply headers with setdefault semantics (proxies may override)."""

    for key, value in build_security_headers(
        enable_hsts=enable_hsts,
        hsts_max_age=hsts_max_age,
        csp=csp,
    ).items():
        response_headers.setdefault(key, value)
