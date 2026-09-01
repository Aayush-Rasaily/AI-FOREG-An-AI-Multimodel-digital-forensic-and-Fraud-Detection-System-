# Signature Verification

Phase 6C adds Siamese signature verification using an EfficientNet-B0 backbone. The service compares questioned signature crops against trusted reference signatures while preserving original evidence hashes.

## Verdicts

| Verdict | Meaning |
| --- | --- |
| `MATCH` | Cosine similarity ≥ configured threshold |
| `NON_MATCH` | Similarity ≤ threshold − inconclusive margin |
| `INCONCLUSIVE` | Similarity falls in the margin band |
| `UNAVAILABLE` | Model weights are not configured or failed integrity checks |

Verdict logic is implemented in `SiameseSignatureModel._verdict` and never fabricates similarity when the model is unavailable.

## API

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/v1/signature/verify` | Verify uploaded or evidence-linked signature pair |
| `GET` | `/api/v1/signature/{verification_id}` | Retrieve one verification run |
| `POST` | `/api/v1/evidence/{evidence_id}/signature-analysis` | Queue verification job (202) |
| `GET` | `/api/v1/evidence/{evidence_id}/signature-analysis` | List verification history |

Multipart form fields for direct verification:

- `reference_file` / `questioned_file` — raw signature images
- `reference_evidence_id` / `questioned_evidence_id` — registered evidence IDs

## Configuration

```env
SIGNATURE_MODEL_ENABLED=true
SIGNATURE_MODEL_PATH=/path/to/siamese-signature.pt
SIGNATURE_MODEL_SHA256=<sha256-of-weights>
SIGNATURE_MODEL_VERSION=1.0.0
SIGNATURE_THRESHOLD=0.80
SIGNATURE_INCONCLUSIVE_MARGIN=0.05
```

When `SIGNATURE_MODEL_PATH` is unset, the API returns `UNAVAILABLE` with `similarity: null` and records reference/questioned hashes for audit.

## Model Integrity

Configured `SIGNATURE_MODEL_SHA256` is validated on load. A mismatch raises `ModelIntegrityError` and prevents inference.

## Frontend

- `SignatureVerificationPanel` in the investigation workspace **Forensics** tab
- Hooks: `useSignatureAnalysisQuery`, `useQueueSignatureAnalysisMutation`
- Service: `frontend/src/services/api/signatureAi.ts`

## Chain of Custody

- Verification runs persist `reference_hash` and `questioned_hash`
- Original evidence files are read-only; prediction JSON is stored as a derived artifact
- Job metadata links questioned and reference evidence IDs
