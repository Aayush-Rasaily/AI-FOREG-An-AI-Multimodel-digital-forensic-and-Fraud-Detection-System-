"""RC2 benchmark suite smoke tests."""

from __future__ import annotations

from scripts.benchmarks.run import run_benchmarks


def test_benchmark_suite_completes() -> None:
    metrics = run_benchmarks(health_iterations=3)
    assert metrics["suite"] == "ai-forge-rc2"
    assert metrics["health_p50_s"] < 2.0
    assert metrics["dummy_ai_p50_s"] < 2.0
    assert metrics["report_build_p50_s"] < 5.0
    assert metrics["startup_s"] < 20.0
