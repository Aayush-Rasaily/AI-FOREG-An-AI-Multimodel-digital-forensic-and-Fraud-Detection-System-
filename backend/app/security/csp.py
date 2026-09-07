"""Content Security Policy builders (Phase 10D)."""

from __future__ import annotations


def api_content_security_policy() -> str:
    """Strict CSP for JSON API responses (no script execution expected)."""

    return (
        "default-src 'none'; "
        "frame-ancestors 'none'; "
        "base-uri 'none'; "
        "form-action 'none'"
    )


def frontend_content_security_policy(
    *,
    allow_inline_styles: bool = True,
) -> str:
    """CSP suitable for the SPA behind nginx (no unsafe-eval)."""

    style_src = "'self' 'unsafe-inline'" if allow_inline_styles else "'self'"
    return (
        "default-src 'self'; "
        f"style-src {style_src}; "
        "script-src 'self'; "
        "img-src 'self' data: blob:; "
        "font-src 'self' data:; "
        "connect-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "frame-ancestors 'none'; "
        "form-action 'self'"
    )
