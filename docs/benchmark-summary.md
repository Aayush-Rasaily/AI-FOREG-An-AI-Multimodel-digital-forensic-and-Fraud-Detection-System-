# Benchmark summary (Phase 10I)

Measured in `tests/test_release_validation.py` on an isolated SQLite/ASGI
harness. These are **readiness bounds**, not production SLOs. Re-run on target
hardware before go-live.

| Probe | Bound in CI | What it represents |
| --- | --- | --- |
| API latency | `GET /health/live` < 2.0 s | Request path + JSON envelope |
| Application startup | `create_app()` < 20.0 s | Import graph + middleware wiring |
| Dummy AI `predict` | CPU time < 2.0 s | Registry/inference infrastructure |
| Peak traced allocations | < 50 MiB during dummy predict | Memory ceiling for infra model |
| Report `build_report_content` | < 5.0 s empty snapshot | Reporting engine without I/O |
| Database throughput | 50 `cases` inserts < 5.0 s | SQLite ORM write path |

## Production guidance

- API p95 for metadata GETs should stay well below the 2 s CI bound when
  PostgreSQL and Redis are local to the region.
- AI modality jobs are asynchronous (`202`); measure queue wait + worker time
  separately ([scalability.md](scalability.md)).
- Report generation on large cases is dominated by aggregation I/O, not the
  empty-snapshot bound above.

No forensic detectors were timed as a competitive score. DummyModel is
infrastructure-only.
