# Case and evidence management

Phase 3 establishes the first persisted forensic data path:

```text
case -> evidence upload -> validation -> staged storage -> SHA-256
     -> final storage -> evidence transaction -> custody event
```

## Case lifecycle

Cases are created with a server-generated internal UUID and public number such
as `CASE-000001`. The default status is `OPEN`. The PATCH endpoint can change
title, description, status, and priority; identifiers and creation timestamps
are immutable.

## Evidence lifecycle

`POST /api/v1/cases/{case_id}/evidence` accepts an untrusted multipart upload.
The service validates the filename, extension, declared MIME type, configured
size limit, and practical file signature checks. The upload is streamed to a
private temporary object, hashed with SHA-256 in bounded chunks, and committed
under a generated storage filename. Client-provided hashes and storage
locations are not accepted.

Evidence metadata uses a server-generated UUID and public number such as
`EVID-000001`. The original filename is retained as metadata, while the stored
filename is generated and the original object is never modified by this phase.
Duplicate bytes within one case are rejected.

## Chain of custody

Successful registration creates an `EVIDENCE_INGESTED` event in the same
database transaction as the evidence record. The initial actor is documented
as `SYSTEM` until authentication is implemented. Each event records the
evidence UUID, UTC timestamp, description, and the calculated SHA-256 hash.

## Storage

The local adapter stores objects under:

```text
data/evidence/<case-id>/<evidence-id>/original/<generated-name>
```

The API exposes no filesystem path or download/delete operation. Local storage
is intended for development and test environments. The `StorageService`
contract is the seam for a future MinIO, S3, or Azure Blob implementation.

## API endpoints

- `POST /api/v1/cases`
- `GET /api/v1/cases?limit=20&offset=0`
- `GET /api/v1/cases/{case_id}`
- `PATCH /api/v1/cases/{case_id}`
- `POST /api/v1/cases/{case_id}/evidence`
- `GET /api/v1/cases/{case_id}/evidence?limit=20&offset=0`
- `GET /api/v1/evidence/{evidence_id}`

Run `uv run alembic -c backend/alembic.ini upgrade head` before using the
endpoints outside Docker Compose. Compose runs the same migration as its
one-shot `migrate` service before starting the API.

> Phase 3 establishes application-level preservation of original evidence.
> Production deployments should use immutable/WORM-capable object storage and
> appropriate access controls for stronger evidentiary guarantees.
