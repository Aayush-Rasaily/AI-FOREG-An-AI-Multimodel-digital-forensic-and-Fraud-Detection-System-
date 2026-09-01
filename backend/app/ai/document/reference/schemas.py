"""Reference comparison schemas."""

from pydantic import BaseModel


class ReferenceComparisonSummary(BaseModel):
    comparison_run_id: str | None
    differences_count: int
