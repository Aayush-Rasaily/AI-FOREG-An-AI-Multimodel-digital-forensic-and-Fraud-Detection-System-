# Phase 6F — Multimodal AI Jury & Evidence Fusion

## Architecture

Evidence flows through existing modality analyzers (forensics, image AI, document AI,
signature AI, video AI, audio AI, comparison). Phase 6F orchestrates their persisted
findings without re-running those engines.

```
Evidence → Modality Findings → Normalization → Aggregation → Jury → Conflicts → Fusion → Assessment
```

Core package: `backend/app/fusion/`

## Finding normalization

`normalization.py` maps each source finding into `NormalizedFinding` with:

- Stable `finding_id` (`{modality}:{source_id}:{analyzer}`)
- Verdict, confidence, severity, availability
- `source_reference` back to the original record

Original finding structures are not modified.

## Modality availability

`ModalityAvailability` values:

- `available`
- `unavailable`
- `not_applicable`
- `failed`
- `insufficient_evidence`

Unavailable modalities are excluded from negative scoring.

## AI jury

`jury.py` implements six deterministic jury roles:

1. Forensic Evidence Analyst
2. Document / Image Specialist
3. Multimedia Specialist
4. Signature Specialist
5. Consistency Analyst
6. Senior Forensic Judge (aggregates specialist votes)

Unavailable findings are not treated as negative evidence.

## Fusion policy

`policy.py` (`ENGINE_VERSION=1.0`, `POLICY_VERSION=1.0`):

- Severity weights: CRITICAL 1.0, HIGH 0.8, MEDIUM 0.5, LOW 0.3, INFO 0.1
- Risk score = weighted suspicious signals / max × 100
- Confidence = mean of available jury/finding confidences
- Senior judge verdict informs final verdict; open conflicts downgrade `genuine` to `inconclusive`
- Unavailable modalities never reduce confidence

## Conflict detection

`conflicts.py` detects verdict disagreement, modality disagreement, confidence spread,
and jury disagreement. Conflicts are persisted and returned in API responses.

## Provenance

Each assessment stores:

- Evidence SHA-256
- Policy/engine versions
- Finding counts
- Links to supporting/contradictory finding IDs

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/evidence/{evidence_id}/fusion-analysis` | Queue fusion job (202) |
| GET | `/api/v1/evidence/{evidence_id}/fusion-analysis` | List runs |
| GET | `/api/v1/evidence/{evidence_id}/fusion-analysis/latest` | Latest assessment |
| GET | `/api/v1/fusion-analysis/{analysis_id}` | One run |
| GET | `/api/v1/evidence/{evidence_id}/fusion-jury` | Jury assessments |
| GET | `/api/v1/evidence/{evidence_id}/fusion-conflicts` | Conflicts |
| GET | `/api/v1/evidence/{evidence_id}/fusion-signals` | Normalized preview |

## Database

Migration `20260831_0011_add_fusion.py` adds:

- `fusion_analysis_runs`
- `jury_assessment_records`
- `fusion_conflict_records`

## Failure handling

- Zero findings → `insufficient_evidence` verdict (no crash)
- Missing/unavailable models → explicit availability states
- Malformed or duplicate findings → deduplicated deterministically
- API returns structured 404/409 errors without stack traces

## Frontend

`AiJuryPanel` in the investigation workspace shows verdict, risk, jury members,
conflicts, modality availability, and provenance.
