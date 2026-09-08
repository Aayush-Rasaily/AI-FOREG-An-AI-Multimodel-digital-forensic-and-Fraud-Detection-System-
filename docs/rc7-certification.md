# Release Candidate certification — AI-Forge v1.0.0 (RC7)

**Version:** 1.0.0  
**Schema head:** `20260915_0034`  
**Certification date:** 2026-09-08  
**Platform:** Windows 10 development host (CI certifies Linux Ubuntu runners)

This document certifies the **Release Candidate** for public v1.0.0.
No features, APIs, or schemas were added in RC7.

## Recommendation

**Approve for production release (RC8 / GitHub tag `v1.0.0`)** provided CI
**Quality gate** is green on `main`. Remaining items are documented in
[known-limitations.md](known-limitations.md) and are non-critical.

## Test summary

| Suite | Result (this certification pass) |
| --- | --- |
| Ruff + format + MyPy | **Ruff: 791 files green.** **MyPy: 735 source files, no issues.** |
| Backend pytest (this pass) | **30 passed** including `test_end_to_end`, RC2 benches, RC3 security, RC5/RC7 artifacts |
| Frontend Vitest (this pass) | **3 passed** (`phase_rc3_security`); full suite is CI-required |
| Frontend production build | **Passed** (`node ./scripts/build.mjs`) |
| Alembic heads | **Single head `20260915_0034`** |
| npm audit | **0** vulnerabilities at `--audit-level=critical` |
| Alembic upgrade/downgrade | Enforced in GitHub Actions PostgreSQL 16 job |
| Docker production build | GitHub Actions `docker.yml`; local daemon may be unavailable |
| Security (RC3 tests + npm audit) | `tests/test_rc3_security.py`; `npm audit --audit-level=critical` |
| Benchmarks (RC2) | `tests/test_rc2_benchmarks.py` / `scripts/benchmarks/run.py` |
| E2E investigation | `tests/test_end_to_end.py` |

Determinism: fusion, correlation, timeline, and reporting consume **stored**
findings and hashes; DummyModel and empty-report benches are repeatable in
process.

## Performance summary

RC2 bounds (in-process, not data-center SLOs): health p50 &lt; 2s, DummyModel
p50 &lt; 2s, empty report p50 &lt; 5s, `create_app` &lt; 20s. See
[performance-rc2.md](performance-rc2.md).

## Security summary

[security-rc3.md](security-rc3.md): authn/authz, uploads, secrets, OpenAPI
off in production, edge metrics hidden. CI fails on **critical** advisories.

## Documentation summary

Guides in [README.md](README.md) match the implemented v1.0 tree. UAT:
[uat-checklist.md](uat-checklist.md) (manual; not a substitute for pytest).

## Cross-platform

| Environment | Status |
| --- | --- |
| Linux (GitHub Actions ubuntu-latest) | Authoritative CI |
| Windows (this host) | `uv` / pytest / Vite supported; Docker optional |
| macOS | Same as other Unix dev hosts; not separately gated |

## UAT

Automated tests cover investigator API workflows. Role-based UI UAT is the
checklist in [uat-checklist.md](uat-checklist.md) for the adopting lab.

## Outstanding known limitations

See [known-limitations.md](known-limitations.md). None compromise chain of
custody of originals or the production fail-closed secret policy.

## Sign-off

| Role | Status |
| --- | --- |
| Engineering (automated gates) | Certified pending green CI on `main` |
| Security review | RC3 documented; no new high/critical items in RC7 |
| Documentation | Complete for v1.0 public release |
| Production release | **Recommended** (tag `v1.0.0`) |
