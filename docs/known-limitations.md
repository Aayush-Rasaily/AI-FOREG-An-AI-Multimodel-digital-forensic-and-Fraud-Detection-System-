# Known limitations — AI-Forge v1.0.0

Items that are **by design** or **operator-owned**, not unresolved critical
defects. They do not weaken original-evidence immutability or production
secret fail-closed behavior.

Security: [security-rc3.md](security-rc3.md). Certification:
[rc7-certification.md](rc7-certification.md).

## Product

- AI and fusion outputs are investigative aids, not legal conclusions.
- Optional OCR, ffprobe, and GPU models are unavailable unless deployed;
  the API reports that fact instead of fabricating results.
- Case listing follows RBAC (`case.view`). Fine-grained isolation uses
  Security Governance case-access records.
- Remember-me stores tokens in browser `localStorage`.
- Sample assets under `samples/` are synthetic and not forensic exhibits.

## Operations

- Public edge Nginx does not expose `/api/v1/metrics`; scrape the API
  service on the private network.
- Schema head is `20260915_0034`. Release cycles after 10I did not add
  migrations.
- Single-region Compose is not a multi-datacenter HA design; see
  [scalability.md](scalability.md) and [disaster-recovery.md](disaster-recovery.md).
- Celery Beat is unused (no periodic schedule).
- Official nginx Alpine still binds port 80 as root; static files are not
  writable.

## Tests / CI

- Full local `pytest tests` can be slow on Windows; GitHub Actions is the
  merge authority.
- Two Vitest files (`phase4.test.tsx`, `phase5b.test.tsx`) may time out on
  constrained Windows hosts; they are not security defects.

## Future work (not in v1.0)

SSO/MFA, additional licensed detectors, and external SIEM connectors are
not implemented. See [ROADMAP.md](../ROADMAP.md).
