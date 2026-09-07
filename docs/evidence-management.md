# Evidence management

Preservation and custody rules for originals and derived artifacts.
Contract details: [case-evidence.md](case-evidence.md),
[processing-pipeline.md](processing-pipeline.md),
[extraction-and-localization.md](extraction-and-localization.md),
[evidence-integrity.md](evidence-integrity.md).

## Register an original

`POST /api/v1/cases/{case_id}/evidence` with multipart field `file`.

The server:

1. Accepts only allow-listed extensions/MIME types and size limits.
2. Computes SHA-256.
3. Stores the object outside the database.
4. Writes `evidence` metadata and a chain-of-custody event.
5. Returns evidence number, hash, status, and identifiers — **not** file
   bytes on GET metadata.

`GET /api/v1/cases/{case_id}/evidence` lists the case. `GET /api/v1/evidence/{id}`
returns metadata and custody history.

Rate limit: upload category (20/minute burst, 200/hour default).

## Processing

`POST /api/v1/evidence/{id}/process` → `202`. Poll
`GET /api/v1/evidence/{id}/processing` and
`GET /api/v1/processing/{job_id}`. Derived files:
`GET /api/v1/evidence/{id}/artifacts`.

Originals stay immutable. Artifacts have independent hashes.

## Extraction

`POST /api/v1/evidence/{id}/extract` queues localization/OCR. Regions:
`GET /api/v1/evidence/{id}/regions`. The platform never invents coordinates.

## Comparison

Register trusted references on the case, then
`POST /api/v1/evidence/{id}/compare`. Differences are stored separately from
the original.

## Integrity

Operators/investigators with `integrity.*` can run case integrity checks and
inspect alerts/drift. This monitors hashes and records; it does not rewrite
history.

## Retention

Legal hold and deletion are administrative decisions. Cleanup scripts must
not drop originals unless policy explicitly allows. See
[maintenance-guide.md](maintenance-guide.md).
