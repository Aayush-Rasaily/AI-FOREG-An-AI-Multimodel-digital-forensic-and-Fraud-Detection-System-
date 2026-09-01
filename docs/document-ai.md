# Document AI Forensics

Phase 6C adds pluggable AI document forensic analysis for PDF and document evidence. The pipeline preserves original evidence bytes and stores derived artifacts separately.

## Detectors

Seven detectors are registered by default:

| Detector | Method | Purpose |
| --- | --- | --- |
| `tampering` | classical | Surfaces manipulation indicators from existing forensic artifacts |
| `text_consistency` | classical | OCR confidence variance across word regions |
| `font_consistency` | classical | Font family and size spread |
| `layout_consistency` | classical | Page dimension and layout variance |
| `logo` | ai | Logo authenticity checks (capability-aware) |
| `metadata` | classical | Producer and metadata anomalies |
| `region_anomaly` | classical | Date, number, and reference inconsistencies |

Enable or disable detectors through `DocumentAISettings.enabled_detectors` without code changes.

## API

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/v1/evidence/{evidence_id}/document-analysis` | Queue document AI analysis (202) |
| `GET` | `/api/v1/evidence/{evidence_id}/document-analysis` | List analysis runs |
| `GET` | `/api/v1/evidence/{evidence_id}/document-findings` | List persisted findings |

Evidence must be processed and extracted before analysis. Original `sha256_hash` is never modified.

## Frontend

- `DocumentAnalysisPanel` in the investigation workspace **Forensics** tab
- Hooks: `useDocumentAnalysisQuery`, `useDocumentFindingsQuery`, `useAnalyzeDocumentMutation`
- Service: `frontend/src/services/api/documentAi.ts`

## Configuration

```env
# Optional GPU preference is inherited from document AI settings
DOCUMENT_AI_ENABLE_GPU=true
```

Detector overrides and timeouts are defined in `backend/app/ai/document/config.py`.

## Chain of Custody

- Analysis jobs record `source_sha256` in job metadata
- Runs store the source hash in `metadata_json`
- Derived heatmaps, masks, overlays, and predictions are stored as artifacts linked to the evidence record
