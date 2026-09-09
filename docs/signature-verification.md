# Signature Verification

Phase 6C adds Siamese signature verification using a **timm EfficientNet-B0**
encoder with a 256-dimensional projection head. The service compares questioned
signature crops against trusted reference signatures while preserving original
evidence hashes.

Packaged production weights live at:

`backend/app/ai/models/signature/siamese_best.pt`

When `SIGNATURE_MODEL_PATH` is unset, that checkpoint is used automatically
(set `SIGNATURE_MODEL_PATH=` empty to force UNAVAILABLE).

## Verdicts

| Verdict | Meaning |
| --- | --- |
| `MATCH` | Cosine similarity ≥ configured threshold |
| `NON_MATCH` | Similarity ≤ threshold − inconclusive margin |
| `INCONCLUSIVE` | Similarity falls in the margin band |
| `UNAVAILABLE` | Model disabled, missing, or failed to load |

Verdict logic is implemented in `SiameseSignatureModel._verdict` and never fabricates similarity when the model is unavailable.

## Preprocessing

- RGB conversion
- Resize to 224×224 (bilinear)
- Scale to `[0, 1]`, ImageNet mean/std normalization
- CHW `float32` tensor

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
SIGNATURE_MODEL_PATH=backend/app/ai/models/signature/siamese_best.pt
SIGNATURE_MODEL_SHA256=<sha256-of-weights>
SIGNATURE_MODEL_VERSION=1.0.0
SIGNATURE_THRESHOLD=0.80
SIGNATURE_INCONCLUSIVE_MARGIN=0.05
SIGNATURE_ENABLE_GPU=true
```

Weights load once per process via a thread-safe singleton (`SignatureModelLoader`).
CUDA is used when available; otherwise CPU.

## Model Integrity

Configured `SIGNATURE_MODEL_SHA256` is validated on load. A mismatch raises
`ModelIntegrityError` for direct loaders; the inference engine maps integrity
failures to `UNAVAILABLE` so the API does not crash.

## Frontend

- `SignatureVerificationPanel` in the investigation workspace **Forensics** tab
- Hooks: `useSignatureAnalysisQuery`, `useQueueSignatureAnalysisMutation`
- Service: `frontend/src/services/api/signatureAi.ts`

## Chain of Custody

- Verification runs persist `reference_hash` and `questioned_hash`
- Original evidence files are read-only; prediction JSON is stored as a derived artifact
- Job metadata links questioned and reference evidence IDs
