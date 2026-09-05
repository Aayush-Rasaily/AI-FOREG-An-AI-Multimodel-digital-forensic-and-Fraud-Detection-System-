"""Deterministic task generation from investigation intelligence."""

from __future__ import annotations

import hashlib
from typing import Any

from backend.app.decision_support.models import (
    TASK_TITLES,
    ProvenanceBundle,
    TaskStatus,
    TaskType,
    WorkflowStage,
    WorkflowTaskDraft,
)
from backend.app.decision_support.policy import (
    GAP_TO_TASK,
    REC_TO_TASK,
    TASK_EFFORT_HOURS,
    TASK_STAGE,
)
from backend.app.decision_support.scoring import (
    priority_from_score,
    task_priority_score,
)


def _key(task_type: str, *parts: str) -> str:
    material = "|".join((task_type, *parts))
    digest = hashlib.sha256(material.encode()).hexdigest()
    return f"dstask_{digest[:24]}"


def generate_tasks(snapshot: dict[str, Any]) -> list[WorkflowTaskDraft]:
    """Build deduplicated investigator tasks from a case snapshot."""

    bucket: dict[str, WorkflowTaskDraft] = {}

    def upsert(
        task_type: TaskType,
        *,
        evidence_ids: list[str],
        description: str,
        severity_boost: float = 0.0,
        intelligence: dict[str, Any] | None = None,
        provenance: ProvenanceBundle | None = None,
    ) -> None:
        eids = sorted({eid for eid in evidence_ids if eid})
        key = _key(task_type.value, *eids[:8], task_type.value)
        score = task_priority_score(
            task_type.value,
            severity_boost=severity_boost,
            support_count=max(1, len(eids)),
        )
        stage = WorkflowStage(TASK_STAGE[task_type.value])
        existing = bucket.get(key)
        if existing is None:
            bucket[key] = WorkflowTaskDraft(
                task_key=key,
                task_type=task_type,
                stage=stage,
                title=TASK_TITLES[task_type],
                description=description,
                priority=priority_from_score(score),
                status=TaskStatus.OPEN,
                estimated_effort_hours=TASK_EFFORT_HOURS[task_type.value],
                required_evidence_ids=eids,
                supporting_intelligence=intelligence or {},
                provenance=provenance or ProvenanceBundle(evidence_ids=tuple(eids)),
                priority_score=score,
            )
            return
        existing.required_evidence_ids = sorted(
            set(existing.required_evidence_ids) | set(eids)
        )
        if score > existing.priority_score:
            existing.priority_score = score
            existing.priority = priority_from_score(score)

    for rec in snapshot.get("recommendations", []):
        code = str(rec.get("code") or "")
        mapped = REC_TO_TASK.get(code)
        if not mapped:
            continue
        upsert(
            TaskType(mapped),
            evidence_ids=list(rec.get("affected_evidence_ids") or []),
            description=str(rec.get("action_text") or TASK_TITLES[TaskType(mapped)]),
            severity_boost={
                "HIGH": 0.12,
                "MEDIUM": 0.05,
                "LOW": 0.0,
            }.get(str(rec.get("priority") or "MEDIUM"), 0.05),
            intelligence={"recommendation_key": rec.get("recommendation_key")},
            provenance=ProvenanceBundle(
                evidence_ids=tuple(
                    sorted(rec.get("affected_evidence_ids") or [])
                ),
                recommendation_ids=tuple(
                    sorted(
                        filter(
                            None,
                            [str(rec.get("recommendation_key") or "")],
                        )
                    )
                ),
                detail=code,
            ),
        )

    for gap in snapshot.get("gaps", []):
        mapped = GAP_TO_TASK.get(str(gap.get("gap_type") or ""))
        if not mapped:
            continue
        upsert(
            TaskType(mapped),
            evidence_ids=list(gap.get("affected_evidence_ids") or []),
            description=str(gap.get("reason") or TASK_TITLES[TaskType(mapped)]),
            severity_boost={
                "HIGH": 0.15,
                "MEDIUM": 0.06,
                "LOW": 0.0,
            }.get(str(gap.get("severity") or "MEDIUM"), 0.06),
            intelligence={"gap_key": gap.get("gap_key")},
            provenance=ProvenanceBundle(
                evidence_ids=tuple(
                    sorted(gap.get("affected_evidence_ids") or [])
                ),
                gap_ids=tuple(
                    sorted(filter(None, [str(gap.get("gap_key") or "")]))
                ),
                detail=str(gap.get("gap_type") or ""),
            ),
        )

    for hyp in snapshot.get("hypotheses", []):
        htype = str(hyp.get("hypothesis_type") or "")
        eids = list(hyp.get("supporting_evidence_ids") or [])
        if htype == "TIMELINE_CONFLICT":
            upsert(
                TaskType.REVIEW_TIMELINE_CONFLICT,
                evidence_ids=eids,
                description=str(hyp.get("explanation") or ""),
                severity_boost=0.12,
                intelligence={"hypothesis_key": hyp.get("hypothesis_key")},
                provenance=ProvenanceBundle(
                    evidence_ids=tuple(sorted(eids)),
                    hypothesis_ids=tuple(
                        sorted(
                            filter(None, [str(hyp.get("hypothesis_key") or "")])
                        )
                    ),
                    timeline_ids=tuple(
                        (hyp.get("provenance") or {}).get("timeline_ids") or ()
                    ),
                ),
            )
        elif htype in {"MISSING_VERIFICATION", "SIGNATURE_INCONSISTENCY"}:
            upsert(
                TaskType.MANUAL_EXPERT_REVIEW,
                evidence_ids=eids,
                description=str(hyp.get("explanation") or ""),
                severity_boost=0.08,
                intelligence={"hypothesis_key": hyp.get("hypothesis_key")},
            )

    if snapshot.get("correlations"):
        eids = sorted(
            {
                str(item.get("left_evidence_id") or "")
                for item in snapshot["correlations"]
            }
            | {
                str(item.get("right_evidence_id") or "")
                for item in snapshot["correlations"]
            }
            - {""}
        )
        upsert(
            TaskType.VALIDATE_CORRELATION,
            evidence_ids=eids,
            description="Validate recorded cross-evidence correlations.",
            severity_boost=0.04,
            provenance=ProvenanceBundle(
                evidence_ids=tuple(eids),
                correlation_ids=tuple(
                    sorted(str(item["id"]) for item in snapshot["correlations"])
                ),
            ),
        )

    if snapshot.get("reports"):
        upsert(
            TaskType.VALIDATE_REPORT,
            evidence_ids=[str(item["id"]) for item in snapshot.get("evidence", [])],
            description="Validate forensic report completeness before closure.",
            severity_boost=0.02,
        )

    coverage = snapshot.get("coverage") or {}
    if float(coverage.get("overall_completeness") or 0) >= 0.85 and not snapshot.get(
        "open_conflicts"
    ):
        upsert(
            TaskType.CLOSE_INVESTIGATION,
            evidence_ids=[str(item["id"]) for item in snapshot.get("evidence", [])],
            description="Coverage thresholds met; prepare investigation closure.",
            severity_boost=0.0,
        )

    if not bucket and not snapshot.get("evidence"):
        upsert(
            TaskType.ACQUIRE_ORIGINAL_EVIDENCE,
            evidence_ids=[],
            description="No evidence registered; acquire initial case evidence.",
            severity_boost=0.15,
        )

    tasks = list(bucket.values())
    tasks.sort(
        key=lambda item: (
            {"HIGH": 0, "MEDIUM": 1, "LOW": 2}[item.priority.value],
            -item.priority_score,
            item.stage.value,
            item.task_type.value,
            item.task_key,
        )
    )
    return tasks
