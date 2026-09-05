# Phase 9E — Case Review, Evidence Validation & Approval

Deterministic case review and evidence validation framework. Organizes peer
review, checklists, multi-role approvals, and validation metrics across the
investigation lifecycle.

**Package / API naming:** `case_review` and `/case-review` (not bare `review`)
to avoid colliding with Phase 8B `/reviews` and Phase 8E `/workflow-reviews`.

## Architecture

```
Evidence · Timeline · Correlation · Fusion · Knowledge Graph
Investigation Intelligence · Decision Support · Reports · Custody
        ↓
Case Review Engine (collect existing outputs only)
        ↓
Evidence Validation signals
        ↓
Review Checklist (suggested statuses — never auto-approved)
        ↓
Approvals (explicit investigator actions)
        ↓
Persist (case_review_* tables)
```

The engine **never re-runs AI models**. It reads stored findings, timelines,
correlations, fusion, knowledge graphs, investigation intelligence,
decision-support workflows, reports, and chain-of-custody events.

Final legal and investigative decisions remain with authorized users.

## Validation Policy

Policy version: `1.0` · Engine version: `9e.1.0`

Checklist codes (deterministic order):

| Code | Title |
|------|-------|
| EVIDENCE_INTEGRITY | Evidence Integrity |
| SHA256_VERIFIED | SHA256 Verified |
| METADATA_VERIFIED | Metadata Verified |
| CHAIN_OF_CUSTODY_COMPLETE | Chain of Custody Complete |
| TIMELINE_REVIEWED | Timeline Reviewed |
| AI_FINDINGS_REVIEWED | AI Findings Reviewed |
| FUSION_REVIEWED | Fusion Reviewed |
| CORRELATIONS_REVIEWED | Correlations Reviewed |
| KNOWLEDGE_GRAPH_REVIEWED | Knowledge Graph Reviewed |
| HYPOTHESES_REVIEWED | Hypotheses Reviewed |
| RECOMMENDATIONS_REVIEWED | Recommendations Reviewed |
| REPORT_REVIEWED | Report Reviewed |
| FINAL_VALIDATION | Final Validation |

Each item stores `status`, optional `reviewer` / `reviewed_at`, `notes`, and
`provenance`. Initial `status` is always `PENDING`. `suggested_status` is
advisory from deterministic signals only.

## Approval Workflow

Required roles (configurable via `REQUIRED_APPROVER_ROLES`):

- `TECHNICAL_REVIEWER`
- `FORENSIC_REVIEWER`
- `LEAD_INVESTIGATOR`
- `CASE_SUPERVISOR`

Decisions: `APPROVED` · `REJECTED` · `CHANGES_REQUESTED` · `DEFERRED`

Approvals are **never** AI-generated. Each record stores reviewer, role,
decision, timestamp, comments, linked checklist (optional), and provenance.

## Review Stages

`PENDING` → `UNDER_REVIEW` → `VALIDATED` / `CHANGES_REQUESTED` →
`APPROVED` / `REJECTED` → `FINALIZED`

Stage inference is rule-based from blocking/outstanding counts, approval
completion, and explicit rejection/changes decisions.

## Metrics

| Metric | Definition |
|--------|------------|
| Validation % | Share of checklist items PASS/NA (status or suggested) |
| Evidence Coverage % | Evidence with SHA-256 / total evidence |
| Review Completion % | Non-PENDING items / total |
| Approval Completion % | Distinct APPROVED required roles / required roles |
| Outstanding Issues | Count of outstanding checklist items |
| Blocking Issues | Count of blocking checklist items |

## Provenance

Every validation and approval records:

- Evidence / timeline / correlation / fusion / knowledge-graph IDs
- Workflow task / hypothesis / recommendation / report IDs
- Policy version, engine version, timestamp

## Persistence

Migration: `20260911_0030_add_case_review.py`

Tables:

- `case_review_runs`
- `case_review_checklists`
- `case_review_checklist_items`
- `case_review_approvals`
- `case_review_validation_records`

## API

| Method | Path |
|--------|------|
| POST | `/cases/{case_id}/case-review` |
| GET | `/cases/{case_id}/case-review` |
| GET | `/cases/{case_id}/case-review/latest` |
| GET | `/cases/{case_id}/case-review/preview` |
| GET | `/cases/{case_id}/case-review/checklist` |
| GET | `/cases/{case_id}/case-review/approvals` |
| GET | `/cases/{case_id}/case-review/metrics` |
| GET | `/cases/{case_id}/case-review/history` |
| GET | `/case-review/{review_id}` |
| PATCH | `/case-review/checklist/{item_id}` |
| POST | `/case-review/approvals` |

Preview validates without persistence. POST creates a new run each time.

Permissions: `case_review.run` · `case_review.view`

## Deterministic Design

- Checklist item keys are SHA-256 digests of code + status hint + notes prefix.
- Collection sorts evidence and related IDs lexicographically.
- Scoring and stage inference are pure functions of stored signals.
- No LLM calls, no model inference, no automated legal conclusions.

## Limitations

- Suggested checklist status is not a legal finding; reviewers must confirm.
- Approval roles are policy-configured, not inferred from Entra/RBAC groups.
- Empty cases produce a blocking evidence-integrity checklist.
- Workflow completion signals come from Phase 9D decision-support metrics when present.
- Does not replace chain-of-custody or report approval workflows from earlier phases.

## Frontend

Workspace tab **Case Review** (`case-review`) renders:

- Review status and validation score
- Checklist with search/filters
- Approval chain form
- Outstanding / blocking issues
- Metrics and review history
- Provenance summary
- Empty / loading / error states
