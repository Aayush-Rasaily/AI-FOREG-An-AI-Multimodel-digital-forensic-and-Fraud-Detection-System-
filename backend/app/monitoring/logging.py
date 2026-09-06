"""Observability logging context helpers (Phase 10B).

Complements ``backend.app.core.logging.JsonFormatter`` without replacing it.
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any

_case_id: ContextVar[str | None] = ContextVar("obs_case_id", default=None)
_evidence_id: ContextVar[str | None] = ContextVar("obs_evidence_id", default=None)
_user_id: ContextVar[str | None] = ContextVar("obs_user_id", default=None)
_trace_id: ContextVar[str | None] = ContextVar("obs_trace_id", default=None)


def set_case_id(case_id: str | None) -> None:
    _case_id.set(case_id)


def set_evidence_id(evidence_id: str | None) -> None:
    _evidence_id.set(evidence_id)


def set_user_id(user_id: str | None) -> None:
    _user_id.set(user_id)


def set_trace_id(trace_id: str | None) -> None:
    _trace_id.set(trace_id)


def get_case_id() -> str | None:
    return _case_id.get()


def get_evidence_id() -> str | None:
    return _evidence_id.get()


def get_user_id() -> str | None:
    return _user_id.get()


def get_trace_id() -> str | None:
    return _trace_id.get()


def clear_observability_context() -> None:
    _case_id.set(None)
    _evidence_id.set(None)
    _user_id.set(None)
    _trace_id.set(None)


def observability_log_fields() -> dict[str, Any]:
    """Return optional structured fields for JSON access logs."""

    fields: dict[str, Any] = {}
    case_id = get_case_id()
    evidence_id = get_evidence_id()
    user_id = get_user_id()
    trace_id = get_trace_id()
    if case_id:
        fields["case_id"] = case_id
    if evidence_id:
        fields["evidence_id"] = evidence_id
    if user_id:
        fields["user_id"] = user_id
    if trace_id:
        fields["trace_id"] = trace_id
    return fields


def extract_ids_from_path(path: str) -> dict[str, str]:
    """Best-effort case/evidence IDs from REST path segments."""

    parts = [segment for segment in path.split("/") if segment]
    found: dict[str, str] = {}
    for index, part in enumerate(parts[:-1]):
        nxt = parts[index + 1]
        if part in {"cases", "case"} and nxt not in {
            "case-review",
            "case-intelligence",
        }:
            found["case_id"] = nxt
        if part in {"evidence", "evidences"}:
            found["evidence_id"] = nxt
    return found
