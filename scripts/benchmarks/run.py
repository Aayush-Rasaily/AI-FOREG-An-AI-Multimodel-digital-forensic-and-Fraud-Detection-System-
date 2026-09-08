"""Repeatable in-process benchmarks (RC2). No forensic scoring changes."""

from __future__ import annotations

import asyncio
import statistics
import time
from typing import Any
from uuid import uuid4

from backend.app.ai.models.dummy import DummyModel
from backend.app.core.config import Settings
from backend.app.main import create_app
from backend.app.reporting.builder import build_report_content


def _empty_report_snapshot() -> dict[str, Any]:
    return {
        "case": {
            "case_id": str(uuid4()),
            "case_number": "CASE-BENCH",
            "title": "Benchmark",
            "status": "OPEN",
        },
        "evidence": [],
        "evidence_hashes": [],
        "analysis_summaries": [],
        "fusion_snapshots": [],
        "case_intelligence": None,
    }


def _percentile(samples: list[float], pct: float) -> float:
    if not samples:
        return 0.0
    ordered = sorted(samples)
    index = min(len(ordered) - 1, max(0, int(round((pct / 100) * (len(ordered) - 1)))))
    return ordered[index]


async def _health_samples(iterations: int = 20) -> list[float]:
    from httpx import ASGITransport, AsyncClient

    settings = Settings(
        debug=True,
        app_env="test",
        database_url="sqlite+aiosqlite://",
        rate_limit_enabled=False,
        rate_limit_use_redis=False,
    )
    app = create_app(settings)
    transport = ASGITransport(app=app)
    durations: list[float] = []
    async with AsyncClient(transport=transport, base_url="http://bench") as client:
        await client.get("/api/v1/health/live")
        for _ in range(iterations):
            started = time.perf_counter()
            response = await client.get("/api/v1/health/live")
            durations.append(time.perf_counter() - started)
            if response.status_code != 200:
                raise RuntimeError(f"health failed: {response.status_code}")
    return durations


def run_benchmarks(*, health_iterations: int = 20) -> dict[str, Any]:
    """Return reproducible local benchmark metrics (seconds)."""

    startup_started = time.perf_counter()
    create_app(
        Settings(
            debug=True,
            app_env="test",
            database_url="sqlite+aiosqlite://",
            rate_limit_enabled=False,
        )
    )
    startup_s = time.perf_counter() - startup_started

    health = asyncio.run(_health_samples(health_iterations))

    model = DummyModel()
    model.load(device="cpu")
    ai_samples: list[float] = []
    for _ in range(10):
        started = time.perf_counter()
        asyncio.run(model.predict({"probe": True}))
        ai_samples.append(time.perf_counter() - started)

    report_samples: list[float] = []
    snapshot = _empty_report_snapshot()
    for _ in range(10):
        started = time.perf_counter()
        build_report_content(
            report_id=str(uuid4()),
            generated_at="2026-09-07T00:00:00+00:00",
            snapshot=snapshot,
        )
        report_samples.append(time.perf_counter() - started)

    return {
        "suite": "ai-forge-rc2",
        "units": "seconds",
        "startup_s": startup_s,
        "health_p50_s": statistics.median(health),
        "health_p95_s": _percentile(health, 95),
        "dummy_ai_p50_s": statistics.median(ai_samples),
        "report_build_p50_s": statistics.median(report_samples),
        "health_samples": len(health),
    }


def main() -> None:
    metrics = run_benchmarks()
    print(metrics)


if __name__ == "__main__":
    main()
