"""Operational analytics collectors from persisted platform tables."""

from __future__ import annotations

from collections import Counter
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.ai import InferenceJob
from backend.app.models.audio_ai import AudioAnalysisRun
from backend.app.models.case import Case
from backend.app.models.correlation import CorrelationAnalysisRun
from backend.app.models.document_ai import DocumentAnalysisRun
from backend.app.models.evidence import Evidence
from backend.app.models.forensic_report import ForensicReport
from backend.app.models.forensics import Finding
from backend.app.models.fusion import FusionAnalysisRun
from backend.app.models.image_ai import ImageAnalysisRun
from backend.app.models.processing import ProcessingJob
from backend.app.models.signature_ai import SignatureVerificationRun
from backend.app.models.timeline import InvestigationTimeline
from backend.app.models.video_ai import VideoAnalysisRun
from backend.app.monitoring.metrics import (
    average,
    duration_ms,
    percentile_95,
    rate,
    status_value,
)


def _job_durations(jobs: list[ProcessingJob]) -> list[float]:
    values: list[float] = []
    for job in jobs:
        value = duration_ms(job.started_at, job.completed_at)
        if value is not None:
            values.append(value)
    return values


def _run_durations(rows: list[Any]) -> list[float]:
    values: list[float] = []
    for row in rows:
        started = getattr(row, "started_at", None)
        completed = getattr(row, "completed_at", None) or getattr(
            row, "finished_at", None,
        )
        latency = getattr(row, "latency_ms", None)
        if isinstance(latency, (int, float)):
            values.append(float(latency))
            continue
        value = duration_ms(started, completed)
        if value is not None:
            values.append(value)
    return values


async def collect_processing_metrics(session: AsyncSession) -> dict[str, Any]:
    """Aggregate processing-job operational metrics."""

    jobs = list(
        await session.scalars(
            select(ProcessingJob).order_by(
                ProcessingJob.created_at.asc(), ProcessingJob.id.asc(),
            )
        )
    )
    status_counts: Counter[str] = Counter(status_value(job.status) for job in jobs)
    created = len(jobs)
    completed = status_counts.get("succeeded", 0)
    failures = status_counts.get("failed", 0)
    retries = sum(1 for job in jobs if int(job.attempt or 0) > 1)
    queued = status_counts.get("queued", 0)
    running = status_counts.get("running", 0)
    queue_durations = [
        duration_ms(job.created_at, job.started_at)
        for job in jobs
        if duration_ms(job.created_at, job.started_at) is not None
    ]
    exec_durations = _job_durations(jobs)
    typed = Counter(
        status_value(job.job_type) for job in jobs
    )
    bottlenecks = [
        {
            "job_id": str(job.id),
            "job_type": status_value(job.job_type),
            "status": status_value(job.status),
            "duration_ms": duration_ms(job.started_at, job.completed_at),
            "attempt": int(job.attempt or 0),
            "error_code": job.error_code,
        }
        for job in sorted(
            [j for j in jobs if status_value(j.status) == "failed"],
            key=lambda row: (str(row.error_code or ""), str(row.id)),
        )[:20]
    ]
    return {
        "jobs_created": created,
        "jobs_completed": completed,
        "failures": failures,
        "retries": retries,
        "queued": queued,
        "running": running,
        "status_counts": dict(sorted(status_counts.items())),
        "job_type_counts": dict(sorted(typed.items())),
        "queue_duration_avg_ms": average(
            [float(v) for v in queue_durations if v is not None]
        ),
        "execution_duration_avg_ms": average(exec_durations),
        "execution_duration_p95_ms": percentile_95(exec_durations),
        "success_rate": rate(completed, created),
        "failure_rate": rate(failures, created),
        "retry_rate": rate(retries, created),
        "recent_failures": bottlenecks,
    }


async def collect_ai_metrics(session: AsyncSession) -> dict[str, Any]:
    """Aggregate AI modality and inference metrics from stored runs."""

    image_rows = list(await session.scalars(select(ImageAnalysisRun)))
    document_rows = list(await session.scalars(select(DocumentAnalysisRun)))
    signature_rows = list(await session.scalars(select(SignatureVerificationRun)))
    video_rows = list(await session.scalars(select(VideoAnalysisRun)))
    audio_rows = list(await session.scalars(select(AudioAnalysisRun)))
    fusion_rows = list(await session.scalars(select(FusionAnalysisRun)))
    inference_rows = list(await session.scalars(select(InferenceJob)))

    def modality_summary(name: str, rows: list[Any]) -> dict[str, Any]:
        statuses: Counter[str] = Counter()
        for row in rows:
            if hasattr(row, "status"):
                statuses[status_value(row.status)] += 1
            elif getattr(row, "error_code", None):
                statuses["failed"] += 1
            else:
                statuses["succeeded"] += 1
        durations: list[float] = []
        for row in rows:
            proc = getattr(row, "processing_time_ms", None)
            if isinstance(proc, (int, float)):
                durations.append(float(proc))
                continue
            single = _run_durations([row])
            durations.extend(single)
        confidences: list[float] = []
        for row in rows:
            conf = getattr(row, "confidence", None)
            if isinstance(conf, (int, float)):
                confidences.append(float(conf))
            sim = getattr(row, "similarity", None)
            if isinstance(sim, (int, float)):
                confidences.append(float(sim))
        unavailable = statuses.get("unavailable", 0)
        failures = statuses.get("failed", 0)
        timeouts = 0
        for row in rows:
            meta = getattr(row, "metadata_json", None)
            if isinstance(meta, dict) and meta.get("timeout"):
                timeouts += 1
            err = str(getattr(row, "error_code", "") or "").lower()
            if "timeout" in err:
                timeouts += 1
        return {
            "modality": name,
            "executions": len(rows),
            "status_counts": dict(sorted(statuses.items())),
            "runtime_avg_ms": average(durations),
            "runtime_p95_ms": percentile_95(durations),
            "confidence_avg": average(confidences),
            "unavailable": unavailable,
            "failures": failures,
            "timeouts": timeouts,
            "failure_rate": rate(failures, len(rows)),
        }

    modalities = [
        modality_summary("image", image_rows),
        modality_summary("document", document_rows),
        modality_summary("signature", signature_rows),
        modality_summary("video", video_rows),
        modality_summary("audio", audio_rows),
        modality_summary("fusion", fusion_rows),
    ]
    detector_failures = sorted(
        [
            {
                "modality": item["modality"],
                "failures": item["failures"],
                "failure_rate": item["failure_rate"],
                "runtime_avg_ms": item["runtime_avg_ms"],
            }
            for item in modalities
        ],
        key=lambda row: (-int(row["failures"]), str(row["modality"])),
    )
    inference_durations = _run_durations(inference_rows)
    return {
        "model_executions": len(inference_rows),
        "modalities": modalities,
        "detector_failure_rankings": detector_failures,
        "average_ai_runtime_ms": average(inference_durations),
        "ai_runtime_p95_ms": percentile_95(inference_durations),
        "total_failures": sum(int(item["failures"]) for item in modalities),
        "total_unavailable": sum(int(item["unavailable"]) for item in modalities),
        "total_timeouts": sum(int(item["timeouts"]) for item in modalities),
    }


async def collect_investigation_metrics(session: AsyncSession) -> dict[str, Any]:
    """Aggregate case/evidence/report/timeline/correlation/fusion counts."""

    cases = list(await session.scalars(select(Case)))
    evidence = list(await session.scalars(select(Evidence)))
    reports = list(await session.scalars(select(ForensicReport)))
    timelines = list(await session.scalars(select(InvestigationTimeline)))
    correlations = list(await session.scalars(select(CorrelationAnalysisRun)))
    fusions = list(await session.scalars(select(FusionAnalysisRun)))
    findings = list(await session.scalars(select(Finding)))

    findings_by_case: Counter[str] = Counter()
    for finding in findings:
        # Finding links via analysis run; use evidence metadata if present.
        evidence_id = getattr(finding, "evidence_id", None)
        if evidence_id is not None:
            findings_by_case[str(evidence_id)] += 1

    evidence_by_case: Counter[str] = Counter(
        str(item.case_id) for item in evidence
    )
    top_cases = [
        {"case_id": case_id, "evidence_count": count}
        for case_id, count in sorted(
            evidence_by_case.items(), key=lambda item: (-item[1], item[0]),
        )[:20]
    ]
    report_durations = _run_durations(reports)
    fusion_durations = _run_durations(fusions)
    correlation_durations = _run_durations(correlations)
    return {
        "cases_created": len(cases),
        "evidence_uploaded": len(evidence),
        "reports_generated": len(reports),
        "timelines_created": len(timelines),
        "correlation_runs": len(correlations),
        "fusion_runs": len(fusions),
        "findings_count": len(findings),
        "top_cases_by_evidence": top_cases,
        "evidence_status_distribution": dict(
            sorted(Counter(status_value(item.status) for item in evidence).items())
        ),
        "case_status_distribution": dict(
            sorted(Counter(status_value(item.status) for item in cases).items())
        ),
        "report_status_distribution": dict(
            sorted(Counter(status_value(item.status) for item in reports).items())
        ),
        "average_report_generation_ms": average(report_durations),
        "average_fusion_runtime_ms": average(fusion_durations),
        "average_correlation_runtime_ms": average(correlation_durations),
        "report_generation_p95_ms": percentile_95(report_durations),
        "fusion_runtime_p95_ms": percentile_95(fusion_durations),
        "correlation_runtime_p95_ms": percentile_95(correlation_durations),
    }


async def collect_kpis(
    processing: dict[str, Any],
    ai: dict[str, Any],
    investigation: dict[str, Any],
) -> dict[str, Any]:
    """Compose operational KPI block from domain aggregates."""

    return {
        "average_processing_time_ms": processing.get("execution_duration_avg_ms"),
        "average_ai_runtime_ms": ai.get("average_ai_runtime_ms"),
        "average_report_generation_time_ms": investigation.get(
            "average_report_generation_ms"
        ),
        "average_fusion_runtime_ms": investigation.get("average_fusion_runtime_ms"),
        "average_correlation_runtime_ms": investigation.get(
            "average_correlation_runtime_ms"
        ),
        "p95_processing_latency_ms": processing.get("execution_duration_p95_ms"),
        "p95_ai_latency_ms": ai.get("ai_runtime_p95_ms"),
        "success_rate": processing.get("success_rate"),
        "failure_rate": processing.get("failure_rate"),
        "retry_rate": processing.get("retry_rate"),
    }
