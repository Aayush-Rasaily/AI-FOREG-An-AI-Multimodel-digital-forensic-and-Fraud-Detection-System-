# Investigation Workflow & Decision Support Engine (Phase 9D)

Additive, deterministic investigator workflow planner that converts investigation
intelligence into tasks, review queues, decision logs, and progress metrics
**without re-running AI models** and **without making legal conclusions**.

## Package naming

Phase 8E already owns `backend/app/workflow/` and the workspace **Workflow** tab.
Phase 8B owns `/cases/{id}/workflow`. Phase 9D therefore lives in:

- Package: `backend/app/decision_support/`
- APIs: `/decision-support` / `/cases/{id}/decision-support*`
- Workspace tab: **Decision Support** (`decision-support`)
- Tables: `decision_support_*` (spec `workflow_tasks` name collides with 8E)

## Architecture

```
Evidence / Timeline / Correlation / Fusion / Knowledge Graph / Intelligence / Reports / Custody
        ↓
   Snapshot collection
        ↓
   Task generation (from gaps, recommendations, hypotheses)
        ↓
   Review queue ordering
        ↓
   Workload metrics
        ↓
   Persist run + tasks + queue; decisions logged separately
```

## Workflow policy

Stages: `NEW`, `TRIAGE`, `COLLECT`, `VERIFY`, `COMPARE`, `AI_ANALYSIS`,
`CORRELATE`, `REVIEW`, `REPORT`, `COMPLETE`.

Each task maps to exactly one stage via fixed policy tables.

## Task generation rules

Recommendations and gaps map to fixed task types (e.g. missing custody →
`COMPLETE_CHAIN_OF_CUSTODY`). Priority uses deterministic base scores plus
severity/support boosts. Titles and descriptions are template/reason text only.

## Review queue rules

Evidence is queued for reasons such as unresolved conflicts, low-confidence
fusion, missing metadata, incomplete custody, and investigation gaps. Ordering
is by priority level then score then evidence id.

## Decision tracking

Investigators record: Accepted/Rejected Recommendation, Marked Reviewed,
Escalated, Deferred, Closed, Reopened — with justification and provenance.
The engine never auto-decides.

## Provenance

Tasks, queue items, and decisions store evidence / timeline / correlation /
fusion / knowledge-graph / hypothesis / recommendation IDs plus engine/policy
versions.

## API

| Method | Path |
|--------|------|
| POST | `/cases/{id}/decision-support` |
| GET | `/cases/{id}/decision-support` |
| GET | `/cases/{id}/decision-support/latest` |
| GET | `/cases/{id}/decision-support/preview` |
| GET | `/cases/{id}/decision-support/tasks` |
| GET | `/cases/{id}/decision-support/review-queue` |
| GET | `/cases/{id}/decision-support/metrics` |
| GET | `/cases/{id}/decision-support/decisions` |
| GET | `/decision-support/{run_id}` |
| PATCH | `/decision-support/tasks/{task_id}` |
| POST | `/decision-support/decisions` |

Permissions: `decision_support.run` / `decision_support.view`.

## Persistence

Migration `20260910_0029`.

## Deterministic design

- Exact rule predicates; stable SHA-256 task/queue keys
- Sorted outputs for repeatability

## Limitations

- Does not replace Phase 8E investigation workflow collaboration UI
- Does not invent legal conclusions or auto-close cases without investigator action
- Best results when Phase 9C intelligence has already been persisted
