# Phase 7B — Cross-Evidence Correlation Engine

## Objective

Phase 7B discovers deterministic relationships between evidence items within a case by reusing existing extraction, AI findings, metadata, signature verification, audio reference comparisons, and Phase 7A timeline timestamps. It does not re-run AI models or duplicate OCR/metadata extraction.

## Architecture

```
Evidence + Extraction + AI Findings + Signature + Audio + Timeline
                         ↓
              CorrelationEngine.build()
                         ↓
         Collect signals → Match → Score → Deduplicate
                         ↓
     correlation_analysis_runs
                         ↓
     evidence_correlations + correlation_support_records
                         ↓
                   Correlation API
                         ↓
            EvidenceCorrelationPanel
```

## Supported Correlation Types

| Type | Score | Source |
|------|-------|--------|
| `same_hash` | 1.00 | Evidence SHA-256 |
| `same_email` | 0.98 | OCR/text extraction |
| `same_phone` | 0.97 | OCR/text extraction |
| `same_qr` | 0.95 | `ExtractionType.QR_CODE` content |
| `same_signature` | 0.92 | Signature verification MATCH |
| `same_location` | 0.90 | EXIF/GPS metadata |
| `same_camera` | 0.90 | EXIF camera model |
| `same_device` | 0.90 | EXIF/device metadata |
| `same_audio_speaker` | 0.88 | Audio reference similarity ≥ 0.7 |
| `same_logo` | 0.86 | Image AI LOGO findings / logo regions |
| `same_document` | 0.85 | Shared document identifiers (INV/ID/REF) |
| `shared_identifier` | 0.82 | Shared OCR identifiers |
| `shared_metadata` | 0.80 | Shared non-camera metadata fields |
| `temporal_overlap` | 0.70 | Phase 7A timeline timestamps |
| `similar_filename` | 0.45 | Filename token Jaccard ≥ 0.5 |

`same_watermark` and `same_person` are **not** implemented — no watermark detector or person-identity model exists in Phases 1–7A.

## Determinism

- Evidence pairs are ordered by smaller UUID → larger UUID
- One relationship per `(pair, correlation_type)` per analysis run
- Results sorted by score desc, type, evidence IDs, correlation_id
- Scoring and confidence come from fixed policy constants

## Provenance

Every correlation stores:

- case / left / right evidence IDs
- supporting finding IDs (extraction, AI, signature, timeline event IDs)
- supporting entities (emails, phones, QR payloads, etc.)
- support records with kind/label/value

No relationship is emitted without a concrete shared signal.

## API

| Method | Route | Description |
|--------|-------|-------------|
| POST | `/api/v1/cases/{case_id}/correlations` | Queue analysis |
| GET | `/api/v1/cases/{case_id}/correlations` | History |
| GET | `/api/v1/cases/{case_id}/correlations/latest` | Latest detail |
| GET | `/api/v1/evidence/{evidence_id}/correlations` | By evidence |
| GET | `/api/v1/correlations/{correlation_id}` | One correlation |

## Concurrency

Partial unique index prevents multiple active (`QUEUED`/`RUNNING`) runs per case. Completed runs remain auditable.

## Relationship to Phase 6G

Case intelligence already emits `duplicate_hash`, `comparison_link`, `signature_verification_link`, and related synthesis relationships. Phase 7B is a separate investigation-intelligence layer with its own tables and broader OCR/metadata/timeline matching. It does not replace Phase 6G.

## Known Limitations

- Email/phone extraction uses regex over stored OCR text; quality depends on prior extraction
- Watermark / person identity correlations are unsupported by current detectors
- Temporal overlap requires a successful Phase 7A timeline run
- Audio speaker correlation requires reference comparison with similarity ≥ 0.7
- Same-hash uploads are normally blocked by case uniqueness; engine still supports the type when hashes match

## Phase 7C

Phase 7C (Entity Resolution) was **not** started.
