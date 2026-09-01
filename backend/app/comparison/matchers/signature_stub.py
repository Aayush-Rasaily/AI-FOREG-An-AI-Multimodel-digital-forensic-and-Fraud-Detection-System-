"""Signature comparison stub — architecture only, no Siamese network."""

from backend.app.comparison.models import ComparisonContext, MatcherResult


class SignatureMatcher:
    """Placeholder matcher for future signature comparison."""

    name = "signature"
    version = "0.0"

    def can_compare(self, context: ComparisonContext) -> bool:
        return False

    async def compare(self, context: ComparisonContext) -> MatcherResult:
        return MatcherResult(
            matcher=self.name,
            version=self.version,
            differences=(),
            metadata={"status": "NOT_IMPLEMENTED"},
        )
