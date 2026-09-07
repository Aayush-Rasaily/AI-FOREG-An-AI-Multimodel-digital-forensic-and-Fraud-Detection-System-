# AI analysis guide

How investigators use modality AI, forensics, and fusion. Architecture:
[ai-architecture.md](ai-architecture.md). This is not a legal playbook.

## Before you run AI

1. Evidence is uploaded and processed.
2. Extraction has completed or reported unavailable capabilities.
3. You understand which modality applies (image vs document vs AV).

## Classic forensics

`POST /api/v1/evidence/{id}/analyze` queues detector orchestration. Review
findings, heatmaps, and the latest summary via the forensics GET routes.

## Modality AI

| Modality | Queue | Results |
| --- | --- | --- |
| Image | `POST .../image-analysis` | findings + regions |
| Document | `POST .../document-analysis` | findings + regions |
| Video | `POST .../video-analysis` | findings, frames, timeline |
| Audio | `POST .../audio-analysis` | findings, segments, features |
| Signature | `POST .../signature-analysis` or `POST /signature/verify` | verification run |

All queue operations return **202**. History endpoints are safe to poll.

Rate limit: AI category (30/minute burst, 300/hour default).

## Fusion (multimodal jury)

`POST /api/v1/evidence/{id}/fusion-analysis` after modality/forensic findings
exist. Inspect latest assessment, jury roles, conflicts, and normalized
signals. Fusion **does not** re-run engines.

## Case-level intelligence

Correlation, entities, timeline, case intelligence, knowledge graph, and
investigation intelligence are **case** operations. They consume stored
products. See [correlation-engine.md](correlation-engine.md),
[timeline-engine.md](timeline-engine.md),
[investigation-intelligence.md](investigation-intelligence.md).

## Models page

`/ai-models` lists registry metadata (`GET /api/v1/models`). Reloading models
is an operations action (`ai.run` / admin practice), not an investigation
shortcut.

## Reading results

- **Unavailable / not applicable / failed** are first-class statuses.
- Confidence is a model score, not a legal burden of proof.
- Conflicts in fusion mean disagreement among sources — record them in the
  report rather than deleting them.
