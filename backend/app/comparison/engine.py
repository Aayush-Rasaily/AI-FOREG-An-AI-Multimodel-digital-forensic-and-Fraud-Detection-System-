"""Plugin registry and orchestration for reference comparison matchers."""

import json
import logging
from typing import Any

from backend.app.application.processors.base import DerivedArtifactPayload
from backend.app.comparison.exceptions import MatcherExecutionError
from backend.app.comparison.matchers import (
    ImageMatcher,
    LayoutMatcher,
    MetadataMatcher,
    PdfMatcher,
    SignatureMatcher,
    TextMatcher,
)
from backend.app.comparison.models import (
    ComparisonContext,
    ComparisonResult,
    ComparisonRunStatus,
    DifferenceItem,
    MatcherResult,
)
from backend.app.domain.processing import ArtifactType

logger = logging.getLogger(__name__)
ENGINE_VERSION = "1.0"


class ComparisonEngine:
    """Run all compatible comparison matcher plugins."""

    def __init__(self, matchers: tuple[Any, ...] | None = None) -> None:
        self.matchers = matchers or default_matchers()

    async def compare(self, context: ComparisonContext) -> ComparisonResult:
        """Execute every compatible matcher and merge differences."""

        differences: list[DifferenceItem] = []
        artifacts: list[DerivedArtifactPayload] = []
        matcher_metadata: dict[str, Any] = {}
        for matcher in self.matchers:
            if not matcher.can_compare(context):
                continue
            try:
                result = await matcher.compare(context)
            except Exception as exc:
                logger.exception(
                    "Matcher failed",
                    extra={
                        "matcher": matcher.name,
                        "questioned_evidence_id": str(context.questioned_evidence_id),
                    },
                )
                raise MatcherExecutionError(
                    "MATCHER_FAILED",
                    f"Matcher {matcher.name} failed during comparison.",
                ) from exc
            differences.extend(result.differences)
            artifacts.extend(result.artifacts)
            artifacts.append(_json_artifact(matcher.name, result))
            matcher_metadata[matcher.name] = {
                "version": result.version,
                **result.metadata,
            }
        return ComparisonResult(
            status=ComparisonRunStatus.SUCCEEDED,
            differences=tuple(differences),
            artifacts=tuple(artifacts),
            metadata={"matchers": matcher_metadata, "engine_version": ENGINE_VERSION},
        )


def default_matchers() -> tuple[Any, ...]:
    """Return the built-in deterministic comparison matcher plugins."""

    return (
        TextMatcher(),
        MetadataMatcher(),
        ImageMatcher(),
        PdfMatcher(),
        LayoutMatcher(),
        SignatureMatcher(),
    )


def _json_artifact(matcher_name: str, result: MatcherResult) -> DerivedArtifactPayload:
    payload = {
        "matcher": matcher_name,
        "version": result.version,
        "differences_count": len(result.differences),
        "metadata": result.metadata,
    }
    return DerivedArtifactPayload(
        artifact_type=ArtifactType.COMPARISON_OUTPUT,
        mime_type="application/json",
        content=json.dumps(payload, sort_keys=True).encode("utf-8"),
        metadata={"matcher": matcher_name},
    )
