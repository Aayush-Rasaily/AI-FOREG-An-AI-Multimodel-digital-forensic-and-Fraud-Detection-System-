"""Workload / progress metrics for decision support."""

from __future__ import annotations

from backend.app.decision_support.models import (
    ReviewQueueDraft,
    WorkflowTaskDraft,
    WorkloadMetrics,
)


def compute_workload(
    tasks: list[WorkflowTaskDraft],
    review_queue: list[ReviewQueueDraft],
    *,
    evidence_total: int,
    overall_completeness: float,
) -> WorkloadMetrics:
    open_tasks = sum(1 for item in tasks if item.status.value == "OPEN")
    completed = sum(1 for item in tasks if item.status.value == "COMPLETED")
    total = len(tasks) or 1
    scores = [item.priority_score for item in tasks]
    avg_priority = round(sum(scores) / len(scores), 4) if scores else 0.0
    critical = sum(
        1 for item in review_queue if item.priority.value == "HIGH"
    )
    workflow_completion = round(completed / total, 4)
    reviewed = len({item.evidence_id for item in review_queue})
    # Coverage of evidence that has been queued (attention), not yet cleared
    review_cov = (
        round(min(1.0, reviewed / evidence_total), 4) if evidence_total else 0.0
    )
    progress = round(
        (0.5 * float(overall_completeness)) + (0.5 * workflow_completion),
        4,
    )
    return WorkloadMetrics(
        open_tasks=open_tasks,
        completed_tasks=completed,
        pending_reviews=len(review_queue),
        average_priority=avg_priority,
        critical_evidence_count=critical,
        workflow_completion=workflow_completion,
        investigation_progress=progress,
        evidence_review_coverage=review_cov,
    )
