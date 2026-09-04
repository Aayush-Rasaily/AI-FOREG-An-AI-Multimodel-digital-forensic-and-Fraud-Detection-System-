# Investigation Intelligence & Hypothesis Engine (Phase 9C)

Additive, deterministic case-level intelligence that generates hypotheses,
identifies evidence gaps, prioritizes recommended actions, and computes
coverage metrics **without re-running AI models**.

## Package naming

Phase 8C already owns `backend/app/intelligence/` (investigation summaries under
`/investigation-summaries`). Phase 9C lives in
`backend/app/investigation_intelligence/` with APIs under
`/investigation-intelligence` and related case routes.

## Architecture

```
Evidence / Timeline / Correlation / Fusion / Knowledge Graph / AI / OCR / Reports / Custody
        ↓
   Snapshot collection (engine.collect)
        ↓
   Coverage metrics
        ↓
   Evidence gap detection
        ↓
   Hypothesis generation + scoring
        ↓
   Recommendation mapping (fixed templates)
        ↓
   Persist run + hypotheses + gaps + recommendations
```

## Hypothesis policy

Hypotheses are rule-based (e.g. timeline conflicts → `TIMELINE_CONFLICT`,
shared identity keys → `SHARED_IDENTITY_INDICATORS`). Confidence uses
deterministic base weights plus support/provenance boosts and contradiction
penalties. **No LLM text.**

## Gap detection rules

Gaps fire from missing custody, metadata, OCR, AI, signature verification,
timeline, knowledge graph, correlations, and comparison targets. Each gap
includes severity, reason, recommended action code, and provenance.

## Recommendation rules

Recommendations are mapped from hypothesis types and gaps to fixed
`RecommendationCode` templates (never free-text AI generation).

## Scoring

- Hypothesis confidence ∈ [0, 1]
- Investigation score ∈ [0, 100] from completeness, conflicts, and high gaps
- Priority ∈ {HIGH, MEDIUM, LOW} from score/severity thresholds

## Provenance

Every hypothesis/gap/recommendation stores evidence, timeline, graph, correlation,
fusion, AI finding, and report IDs plus engine/policy versions.

## API

| Method | Path |
|--------|------|
| POST | `/cases/{id}/investigation-intelligence` |
| GET | `/cases/{id}/investigation-intelligence` |
| GET | `/cases/{id}/investigation-intelligence/latest` |
| GET | `/investigation-intelligence/{run_id}` |
| GET | `/cases/{id}/hypotheses` |
| GET | `/cases/{id}/evidence-gaps` |
| GET | `/cases/{id}/recommendations` |
| GET | `/cases/{id}/investigation-summary` |
| GET | `/cases/{id}/investigation-preview` (no persist) |

Permissions: `investigation_intelligence.run` / `investigation_intelligence.view`.

## Persistence

Migration `20260909_0028` (spec `20260901_00XX` band exhausted).

Tables: `investigation_intelligence_runs`, `investigation_hypotheses`,
`evidence_gap_records`, `investigation_recommendations`.

## Deterministic design

- Exact rule predicates only
- Stable keys via SHA-256 prefixes
- Sorted outputs for repeatability

## Limitations

- Does not invent entities or re-run detectors
- AI finding signals depend on stored detector/category/description text
- Completeness is coverage-oriented, not a guilt/innocence verdict
- Coexists with Phase 6G case intelligence and Phase 8C summaries
