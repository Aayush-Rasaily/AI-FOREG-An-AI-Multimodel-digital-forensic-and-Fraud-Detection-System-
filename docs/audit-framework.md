# Phase 7E — Audit, Compliance & Evidence Integrity Framework

## Overview

Comprehensive audit trail recording every investigator action, analysis event, report generation, and system operation. Immutable, deterministic, and exportable.

No forensic or AI analysis logic is modified.

## Architecture

```
events.py     →  recorder.py  →  repository.py  →  service.py  →  API
integrity.py  →  service.py
exporters.py  →  service.py
```

### Modules

| File | Purpose |
|---|---|
| `events.py` | Build audit event dicts with integrity hashes |
| `recorder.py` | Persist audit events to the database |
| `repository.py` | Query audit events with filtering |
| `service.py` | Application service (record, list, verify, export) |
| `integrity.py` | Evidence and report checksum verification |
| `exporters.py` | Export audit logs as canonical JSON |
| `policy.py` | Engine/policy version constants |
| `models.py` | Domain models (categories, integrity status) |
| `schemas.py` | Pydantic API schemas |
| `exceptions.py` | Domain exceptions |

## Audit Record Fields

Every event stores:

- **Audit ID** — UUID
- **Timestamp** — UTC ISO 8601
- **User** — Actor identifier
- **Operation** — Event type (e.g. `case.created`, `evidence.uploaded`)
- **Category** — Top-level grouping (case, evidence, analysis, report, user, system)
- **Case ID** — Optional reference
- **Evidence ID** — Optional reference
- **Previous state** — JSON snapshot before change
- **New state** — JSON snapshot after change
- **Client IP** — Request origin
- **User Agent** — Client identifier
- **Engine Version** — Audit engine version
- **Policy Version** — Compliance policy version
- **SHA-256 Checksum** — Content hash if applicable
- **Integrity Hash** — Deterministic SHA-256 of the event record
- **Metadata** — Additional context

## Supported Operations

- `case.created`, `evidence.uploaded`, `evidence.deleted`
- `metadata.extraction`, `ocr.execution`, `pattern.extraction`
- `ai.analysis`, `fusion.analysis`
- `timeline.generation`, `correlation.generation`, `entity.generation`
- `report.generation`
- `user.download`, `user.export`, `user.login`, `user.logout`
- `permission.changed`, `configuration.updated`, `migration.executed`

## Evidence Integrity Verification

Deterministic verification without modifying stored evidence:

- **Evidence SHA-256** — Verified against ingestion hash
- **Report checksum** — Recomputed from content and compared to stored value

## Compliance Alignment

- **ISO 27037** — Digital evidence handling
- **NIST SP 800-86** — Forensic analysis guidelines
- Immutable audit history (append-only)
- Exportable audit logs with checksum

## API

| Method | Path | Description |
|---|---|---|
| GET | `/audit` | List all audit events (filterable) |
| GET | `/audit/{id}` | Get one audit event |
| GET | `/cases/{case_id}/audit` | List audit events for a case |
| GET | `/evidence/{id}/audit` | List audit events for evidence |
| POST | `/audit/verify` | Verify integrity checksums |
| GET | `/audit/export` | Export audit log as JSON |

## Frontend

The `AuditTrailPanel` component provides:

- Chronological event display
- Search/filter by operation, category, user
- Expandable event detail (state changes, integrity hash)
- Integrity verification button
- Export button
- Compliance status badges

Integrated into the Investigation Workspace as the "Audit Trail" tab.

## Determinism

- Integrity hashes use canonical JSON with sorted keys
- Same inputs always produce the same hash
- Events are immutable once recorded
- Export includes a checksum header
