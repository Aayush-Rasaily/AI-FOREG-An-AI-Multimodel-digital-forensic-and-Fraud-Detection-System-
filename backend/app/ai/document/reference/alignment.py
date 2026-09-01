"""Reference alignment helpers for document comparison."""

from __future__ import annotations


def align_page_numbers(
    questioned_pages: int,
    reference_pages: int,
) -> dict[str, int]:
    """Return simple page alignment metadata."""

    return {
        "questioned_pages": questioned_pages,
        "reference_pages": reference_pages,
        "aligned_pages": min(questioned_pages, reference_pages),
    }
