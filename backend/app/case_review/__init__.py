"""Phase 9E case review & evidence validation framework.

Package name is `case_review` to avoid colliding with Phase 8B/8E
collaboration and workflow review APIs under `/reviews` and `/workflow-reviews`.
"""

from backend.app.case_review.service import CaseReviewService

__all__ = ["CaseReviewService"]
