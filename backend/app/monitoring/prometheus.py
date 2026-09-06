"""Prometheus metric registry and exposition helpers (Phase 10B)."""

from __future__ import annotations

from typing import Any

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

# Process-local registry (safe for tests and single-process uvicorn).
REGISTRY = CollectorRegistry(auto_describe=True)

REQUEST_COUNT = Counter(
    "ai_forge_http_requests_total",
    "Total HTTP requests",
    ("method", "path", "status"),
    registry=REGISTRY,
)
REQUEST_LATENCY = Histogram(
    "ai_forge_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ("method", "path"),
    registry=REGISTRY,
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
AI_EXECUTION = Histogram(
    "ai_forge_ai_execution_duration_seconds",
    "AI detector/engine execution duration",
    ("modality",),
    registry=REGISTRY,
)
PROCESSING_DURATION = Histogram(
    "ai_forge_processing_duration_seconds",
    "Evidence processing job duration",
    ("job_type",),
    registry=REGISTRY,
)
QUEUE_LENGTH = Gauge(
    "ai_forge_queue_length",
    "Approximate background/processing queue length",
    ("queue",),
    registry=REGISTRY,
)
DB_QUERIES = Counter(
    "ai_forge_db_queries_total",
    "Database query executions observed by instrumentation",
    ("operation",),
    registry=REGISTRY,
)
REDIS_OPS = Counter(
    "ai_forge_redis_operations_total",
    "Redis operations observed by instrumentation",
    ("command",),
    registry=REGISTRY,
)
PROCESS_MEMORY_BYTES = Gauge(
    "ai_forge_process_memory_bytes",
    "Process resident memory in bytes",
    registry=REGISTRY,
)
PROCESS_CPU_RATIO = Gauge(
    "ai_forge_process_cpu_ratio",
    "Process CPU utilization ratio (0-1 approximate)",
    registry=REGISTRY,
)
GPU_AVAILABLE = Gauge(
    "ai_forge_gpu_available",
    "Whether a GPU device is available (1/0)",
    registry=REGISTRY,
)
MODEL_LOADS = Counter(
    "ai_forge_model_loads_total",
    "Model load attempts",
    ("model", "status"),
    registry=REGISTRY,
)
OCR_DURATION = Histogram(
    "ai_forge_ocr_duration_seconds",
    "OCR extraction duration",
    registry=REGISTRY,
)
VIDEO_ANALYSIS_DURATION = Histogram(
    "ai_forge_video_analysis_duration_seconds",
    "Video analysis duration",
    registry=REGISTRY,
)
AUDIO_ANALYSIS_DURATION = Histogram(
    "ai_forge_audio_analysis_duration_seconds",
    "Audio analysis duration",
    registry=REGISTRY,
)
FUSION_DURATION = Histogram(
    "ai_forge_fusion_duration_seconds",
    "Fusion analysis duration",
    registry=REGISTRY,
)
CORRELATION_DURATION = Histogram(
    "ai_forge_correlation_duration_seconds",
    "Correlation analysis duration",
    registry=REGISTRY,
)
REPORT_DURATION = Histogram(
    "ai_forge_report_generation_duration_seconds",
    "Report generation duration",
    registry=REGISTRY,
)


def normalize_path(path: str) -> str:
    """Collapse high-cardinality path segments for metric labels."""

    parts = [segment for segment in path.split("/") if segment]
    normalized: list[str] = []
    for part in parts:
        if len(part) >= 32 or _looks_like_id(part):
            normalized.append("{id}")
        else:
            normalized.append(part)
    return "/" + "/".join(normalized) if normalized else "/"


def _looks_like_id(value: str) -> bool:
    if value.count("-") >= 4 and len(value) >= 32:
        return True
    return value.isdigit()


def observe_request(
    *,
    method: str,
    path: str,
    status: int,
    duration_seconds: float,
) -> None:
    label_path = normalize_path(path)
    REQUEST_COUNT.labels(method=method, path=label_path, status=str(status)).inc()
    REQUEST_LATENCY.labels(method=method, path=label_path).observe(duration_seconds)


def observe_domain_duration(kind: str, seconds: float, *, label: str = "") -> None:
    """Record a domain-specific duration histogram."""

    mapping: dict[str, Any] = {
        "ai": AI_EXECUTION,
        "processing": PROCESSING_DURATION,
        "ocr": OCR_DURATION,
        "video": VIDEO_ANALYSIS_DURATION,
        "audio": AUDIO_ANALYSIS_DURATION,
        "fusion": FUSION_DURATION,
        "correlation": CORRELATION_DURATION,
        "report": REPORT_DURATION,
    }
    metric = mapping.get(kind)
    if metric is None:
        return
    if kind in {"ai", "processing"}:
        metric.labels(label or "unknown").observe(seconds)
    else:
        metric.observe(seconds)


def set_queue_length(queue: str, length: int) -> None:
    QUEUE_LENGTH.labels(queue=queue).set(max(0, length))


def record_db_query(operation: str = "query") -> None:
    DB_QUERIES.labels(operation=operation).inc()


def record_redis_op(command: str = "cmd") -> None:
    REDIS_OPS.labels(command=command).inc()


def record_model_load(model: str, *, success: bool) -> None:
    MODEL_LOADS.labels(model=model, status="ok" if success else "error").inc()


def refresh_runtime_gauges() -> None:
    """Best-effort process resource gauges (no external agents required)."""

    try:
        import psutil

        proc = psutil.Process()
        PROCESS_MEMORY_BYTES.set(float(proc.memory_info().rss))
        PROCESS_CPU_RATIO.set(float(proc.cpu_percent(interval=None) / 100.0))
    except Exception:  # noqa: BLE001
        pass

    gpu = 0.0
    try:
        import torch

        if bool(getattr(torch, "cuda", None) and torch.cuda.is_available()):
            gpu = 1.0
    except Exception:  # noqa: BLE001
        gpu = 0.0
    GPU_AVAILABLE.set(gpu)


def render_prometheus_metrics() -> tuple[bytes, str]:
    """Return Prometheus exposition payload and content type."""

    refresh_runtime_gauges()
    return generate_latest(REGISTRY), CONTENT_TYPE_LATEST
