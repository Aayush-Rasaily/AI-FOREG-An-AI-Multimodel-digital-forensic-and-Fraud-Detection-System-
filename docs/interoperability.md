# Digital Evidence Exchange & Interoperability (Phase 9A)

Additive import/export layer for exchanging AI-Forge investigations with
other forensic tools using **standardized, deterministic** packages.

Does **not** regenerate forensic analyses. Does **not** overwrite existing
investigations on import.

## Package structure

A JSON Investigation Package ZIP contains (stable paths, sorted members):

```
manifest.json
case.json
evidence/index.json
evidence/{id}.json
custody/events.json
extractions/index.json
ai/summaries.json
fusion/summaries.json
correlation/summaries.json
timeline/timeline.json          # when present
reports/index.json
workflow/status.json            # when present
security/metadata.json          # when present
evidence/binaries/{id}.bin      # optional
```

Other formats:

| Format | Contents |
| --- | --- |
| `csv` | `case.csv`, `evidence.csv`, `manifest.json` |
| `pdf_bundle` | Existing PDF bytes under `reports/pdf/` (no re-render) |
| `zip_evidence` | Case/evidence metadata + custody + binaries |
| `manifest` | `checksums.json` + `manifest.json` |

## Manifest schema

Required keys: `package_version`, `schema_version`, `created_at`,
`evidence_count`, `report_count`, `timeline_count`, `files`,
`package_checksum`, `policy_versions`.

Each `files[]` entry: `{ "path", "sha256" }`.

`package_checksum` = SHA-256 of sorted `path:sha256` lines.

`manifest_checksum` = SHA-256 of canonical JSON (sorted keys) after
`package_checksum` is set.

Provenance block records export version, evidence IDs, report versions,
timeline version, policy versions, package and manifest checksums.

## Checksum process

1. Serialize each member with canonical JSON (sorted keys) or raw bytes.
2. Hash each member (SHA-256).
3. Compute package checksum from sorted digests.
4. Finalize manifest + manifest checksum.
5. Build ZIP with **fixed ZipInfo date** `(2020-01-01)` and sorted members
   so identical payloads yield identical archive bytes.
   Documented non-determinism: only `created_at` inside the manifest
   (and therefore checksums that include it) when wall-clock differs.

## Import validation

Validates: schema keys, schema/package version, per-file hashes, package
checksum, optional manifest checksum, required metadata, duplicate
`case_id` / `case_number`.

**Never overwrites** existing investigations. Conflicts set job status
`CONFLICTS` and integrity `CONFLICTS`.

## API endpoints

| Method | Path | Permission |
| --- | --- | --- |
| POST | `/cases/{case_id}/export` | `interop.export` |
| POST | `/cases/import` | `interop.import` |
| GET | `/exports` | `interop.export` |
| GET | `/exports/{id}` | `interop.export` |
| GET | `/exports/{id}/manifest` | `interop.export` |
| GET | `/exports/{id}/download` | `interop.export` |
| GET | `/imports` | `interop.import` |
| GET | `/imports/{id}` | `interop.import` |

## Database

Migration: `20260907_0026` (spec `20260901_0019` was already used).

Tables store **metadata only**: `export_jobs`, `import_jobs`,
`package_manifests`.

## Guarantees

- Deterministic member ordering and ZIP timestamps
- Provenance preserved in manifest
- No automatic overwrite on import
- Reuses existing reports/evidence; does not re-run AI/fusion engines
- Additive to Phases 1–8G

UI: Investigation Workspace → **Exchange**; Administration → **Exchange**.
