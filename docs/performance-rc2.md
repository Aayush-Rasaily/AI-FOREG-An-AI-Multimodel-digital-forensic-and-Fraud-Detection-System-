# RC2 performance and benchmarking

Stabilization follow-on to Phase 10C. **No forensic scoring, hashing, or API
contract changes.**

## Test environment (local CI-style)

- Python 3.12, in-process FastAPI via `httpx` ASGI
- SQLite for isolated API samples (production uses PostgreSQL)
- DummyModel CPU inference (infrastructure only)
- Empty-case report builder (aggregation CPU, not large-case I/O)

Hardware is the developer/CI runner; treat numbers as **regression bounds**,
not data-center SLOs.

## Methodology

```bash
uv run python scripts/benchmarks/run.py
uv run pytest tests/test_rc2_benchmarks.py tests/test_release_validation.py -q
```

Suite records:

| Metric | What |
| --- | --- |
| `startup_s` | `create_app()` wall time |
| `health_p50_s` / `health_p95_s` | `GET /api/v1/health/live` |
| `dummy_ai_p50_s` | DummyModel.predict |
| `report_build_p50_s` | `build_report_content` empty snapshot |

## Before / after (RC2)

| Change | Effect |
| --- | --- |
| GZip on non-debug API | Smaller JSON/HTML over the wire; tests keep `debug=True` uncompressed |
| Existing 10C indexes / cache / thread pool | Unchanged; still the production query path |
| Windows SelectorEventLoop in pytest | Avoids psycopg Proactor failures; not a prod algorithm change |
| Frontend TestProviders session | Tests no longer stall on `/login`; runtime UX unchanged |

Recommended sizing remains [scalability.md](scalability.md): stateless API
replicas, workers by queue, PostgreSQL pool budget vs replica count.

## Large-evidence guidance

CI does not ingest multi-hour video. For staging, upload representative
batches and watch Prometheus HTTP histograms plus worker queue depth. Fusion
and correlation remain **deterministic** over persisted findings.
