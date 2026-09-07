"""Changelog and release-note generation (Phase 10G)."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime


def generate_changelog_section(
    version: str,
    commits: Iterable[str],
    *,
    released_at: datetime | None = None,
) -> str:
    """Render a SemVer changelog section from conventional-ish commit subjects."""

    stamp = (released_at or datetime.now(UTC)).date().isoformat()
    lines = [f"## {version} — {stamp}", ""]
    features: list[str] = []
    fixes: list[str] = []
    other: list[str] = []
    for raw in commits:
        subject = raw.strip()
        if not subject:
            continue
        lowered = subject.lower()
        if lowered.startswith("feat"):
            features.append(f"- {subject}")
        elif lowered.startswith("fix"):
            fixes.append(f"- {subject}")
        else:
            other.append(f"- {subject}")
    if features:
        lines.extend(["### Features", *features, ""])
    if fixes:
        lines.extend(["### Fixes", *fixes, ""])
    if other:
        lines.extend(["### Other", *other, ""])
    if not features and not fixes and not other:
        lines.append("- Maintenance release.")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def prepend_changelog(existing: str, section: str) -> str:
    """Insert a new version section after the changelog title."""

    header = "# Changelog\n"
    body = existing
    if existing.lstrip().startswith("# Changelog"):
        remainder = existing.split("\n", 1)
        body = remainder[1] if len(remainder) > 1 else ""
    return header + "\n" + section.rstrip() + "\n" + body.lstrip("\n")
