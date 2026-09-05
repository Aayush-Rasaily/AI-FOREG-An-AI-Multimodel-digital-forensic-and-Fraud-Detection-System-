"""Workflow planner — orchestrates tasks, queue, and metrics."""

from __future__ import annotations

from typing import Any

from backend.app.decision_support.models import WorkflowPlan, WorkflowStage
from backend.app.decision_support.policy import DS_ENGINE_VERSION, DS_POLICY_VERSION
from backend.app.decision_support.review_queue import build_review_queue
from backend.app.decision_support.task_generator import generate_tasks
from backend.app.decision_support.workload import compute_workload


def _infer_stage(tasks: list) -> WorkflowStage:
    if not tasks:
        return WorkflowStage.NEW
    # Prefer earliest unfinished stage in pipeline order
    order = [item.value for item in WorkflowStage]
    open_stages = {
        item.stage.value
        for item in tasks
        if item.status.value != "COMPLETED"
    }
    if not open_stages:
        return WorkflowStage.COMPLETE
    for stage in order:
        if stage in open_stages:
            return WorkflowStage(stage)
    return WorkflowStage.TRIAGE


def plan_workflow(snapshot: dict[str, Any]) -> WorkflowPlan:
    """Produce a deterministic investigator workflow plan."""

    tasks = generate_tasks(snapshot)
    queue = build_review_queue(snapshot)
    coverage = snapshot.get("coverage") or {}
    evidence_rows = snapshot.get("evidence") or []
    metrics = compute_workload(
        tasks,
        queue,
        evidence_total=int(
            coverage.get("evidence_total") or len(evidence_rows)
        ),
        overall_completeness=float(coverage.get("overall_completeness") or 0),
    )
    return WorkflowPlan(
        tasks=tasks,
        review_queue=queue,
        metrics=metrics,
        current_stage=_infer_stage(tasks),
        open_conflicts=list(snapshot.get("open_conflicts") or []),
        provenance={
            "engine_version": DS_ENGINE_VERSION,
            "policy_version": DS_POLICY_VERSION,
            "sources": sorted(snapshot.get("source_kinds") or []),
            "evidence_count": len(snapshot.get("evidence") or []),
        },
    )
