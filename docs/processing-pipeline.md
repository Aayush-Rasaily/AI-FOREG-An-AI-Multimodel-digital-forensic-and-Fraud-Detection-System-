# Phase 4: Evidence Processing Pipeline

Phase 4 prepares registered evidence for later forensic analysis. It does not
run OCR, machine-learning models, forensic detectors, fraud scoring, or
produce authenticity verdicts.

## Architecture

The version-one pipeline is:

```text
Evidence
  -> PREPROCESSING job (QUEUED)
  -> read-only integrity inspection
  -> broad file classification
  -> safe basic metadata extraction
  -> preview manifest generation
  -> independently hashed artifacts
  -> Evidence READY_FOR_ANALYSIS
```

`ProcessingOrchestrator` owns lifecycle and transaction coordination. It
does not contain file-analysis algorithms. Processors implement the
`EvidenceProcessor` contract:

```python
def can_process(context: ProcessorContext) -> bool: ...
async def process(context: ProcessorContext) -> ProcessorResult: ...
```

The initial processors are `FileInspectionProcessor`,
`FileClassificationProcessor`, `MetadataProcessor`, and `PreviewProcessor`.
They are ordered deterministically and can be replaced or extended without
changing the API or job runner.

## Job lifecycle

Jobs use controlled types and statuses. A local development runner executes
the queued job through a FastAPI background task; a future worker can call the
same `ProcessingOrchestrator.run(job_id)` method.

```text
QUEUED -> RUNNING -> SUCCEEDED
                   -> FAILED
QUEUED/RUNNING -> CANCELLED
```

Each job records its attempt and safe terminal error code/message. Automatic
retries are intentionally not enabled. A partial unique index prevents two
`QUEUED` or `RUNNING` jobs with the same evidence and job type. Completed
processing may be explicitly requested again.

## Original versus derived data

The registered original is read only. Inspection opens it in binary read mode
and streams a SHA-256 calculation against the registered hash and size. The
pipeline never writes to the original key.

Derived objects are stored separately:

```text
data/evidence/<case-id>/<evidence-id>/original/<stored-file>
data/evidence/<case-id>/<evidence-id>/artifacts/<artifact-id>.artifact
```

Every persisted artifact has a server-calculated storage key, MIME type, size,
and SHA-256 hash. API responses intentionally omit storage paths.

Phase 4 currently generates JSON metadata and preview manifests as safe,
format-neutral derivatives. Format-specific binary thumbnails and media
duration/dimensions can be added as isolated safe adapters later.

## Custody and evidence status

Processing records `PROCESSING_STARTED`, `ARTIFACT_CREATED`,
`PROCESSING_COMPLETED`, or `PROCESSING_FAILED` custody events. Events identify
the evidence and include the evidence or artifact hash where applicable.

Successful processing changes `REGISTERED` to `READY_FOR_ANALYSIS`. A failed
job marks the record `FAILED` while retaining the original object and its
registered evidence row. It never marks evidence as analyzed.

## API

- `POST /api/v1/evidence/{evidence_id}/process`
- `GET /api/v1/evidence/{evidence_id}/processing`
- `GET /api/v1/processing/{job_id}`
- `GET /api/v1/evidence/{evidence_id}/artifacts`

Processing failures expose stable safe codes such as
`EVIDENCE_FILE_MISSING`, `EVIDENCE_INTEGRITY_MISMATCH`, and
`PROCESSOR_FAILED`. Stack traces and filesystem paths remain server-side.

## Future worker integration

The API currently queues a local development job. A production deployment can
replace the background-task adapter with a queue/worker boundary that
deserializes the UUID and invokes the same orchestration service. Processor
contracts, artifact storage, custody events, and lifecycle transitions do not
need to change. Future forensic processors should be added only in later
phases and must continue to consume read-only originals or derived copies.
