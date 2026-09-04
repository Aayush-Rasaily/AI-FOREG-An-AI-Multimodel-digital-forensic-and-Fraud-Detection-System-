# Investigation Knowledge Graph (Phase 9B)

Additive, deterministic knowledge-graph layer that connects people,
organizations, devices, files, identifiers, timeline events, AI findings,
and evidence **without re-running AI models**.

Coexists with Phase 7C Entity Graph (`/entities`). This module uses distinct
tables and `/knowledge-graph` APIs.

## Architecture

```
Evidence / Extraction / OCR / AI findings / Timeline / Correlation / Fusion
        ↓
   Candidate extraction (graph_builder)
        ↓
   Exact-key entity resolution (entity_resolution)
        ↓
   Relationship builder + scoring
        ↓
   Persist (knowledge_graph_runs + graph_*)
```

## Entity resolution policy

- Exact identity keys only (email, phone, SHA-256, IMEI/MAC/serial when present,
  filename+hash, GPS/QR when present).
- **No fuzzy AI / LLM merging.**
- Multi-hit exact merges record combined provenance and a small deterministic
  confidence boost.
- Stable entity IDs = `sha256(type|normalized_key)` prefix.

## Relationship policy

Supported types include `USES_DEVICE`, `OWNS`, `CREATED`, `SENT`, `RECEIVED`,
`LOCATED_AT`, `CAPTURED_BY`, `REFERENCES`, `DERIVED_FROM`, `SIMILAR_TO`,
`CORRELATED_WITH`, `SHARES_IDENTIFIER`, `MENTIONS`, `CONNECTED_TO`,
`PART_OF`, `SUPPORTS`, `CONTRADICTS`, `OBSERVED_AT`, `ASSOCIATED_WITH`.

Edges are deduplicated by `(source, target, type)`. Confidence/weight come
from base type weights plus support/provenance boosts (`scoring.py`).

## Provenance

Every entity/edge stores source kind/id plus optional evidence, finding,
timeline, correlation, fusion, OCR/metadata fields, timestamps, engine and
policy versions.

## API

| Method | Path | Permission |
| --- | --- | --- |
| POST | `/cases/{id}/knowledge-graph` | `knowledge_graph.run` |
| GET | `/cases/{id}/knowledge-graph` | `knowledge_graph.view` |
| GET | `/cases/{id}/knowledge-graph/preview` | `knowledge_graph.view` (no persist) |
| GET | `/knowledge-graph/{graph_id}` | view |
| GET | `/knowledge-graph/entities` | view |
| GET | `/knowledge-graph/relationships` | view |
| GET | `/knowledge-graph/entity/{id}` | view |
| GET | `/knowledge-graph/entity/{id}/neighbors` | view |
| GET | `/knowledge-graph/search?q=` | view |

## Persistence

Migration: `20260908_0027` (spec `20260901_00XX` band exhausted).

Tables: `knowledge_graph_runs`, `graph_entities`, `graph_relationships`,
`graph_entity_aliases`, `graph_provenance`.

## Deterministic design

- Sorted candidate merges and edge ordering
- Stable IDs from content hashes
- Identical investigation outputs → identical graph topology/keys
  (run UUID / created_at differ per build)

## Limitations

- Identifier extraction from free text uses deterministic regex (not NLP).
- Modality AI findings currently load image/document tables; other modalities
  can be added additively.
- Preview never persists; build creates a new run each time.
- Visualization is an SVG circular layout (no new graph library dependency).

## UI

Investigation Workspace → **Knowledge Graph** tab.
