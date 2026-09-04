# Investigation Workflow, Review & Collaboration (Phase 8E)

Phase 8E adds a deterministic investigation lifecycle layer for AI-Forge.
It manages investigation status progression, tasks, evidence/report reviews,
milestones, notes, in-app notifications, and a complete audit trail.

It is **strictly additive**. Phase 8B collaboration APIs
(`/cases/{id}/workflow`, `/tasks`, `/reviews`, `/notifications`) remain
unchanged. Phase 8E uses namespaced routes to avoid collisions (same pattern
as Phase 8C `/investigation-summaries`).

## Architecture

```
WorkflowService
  ├── engine (validated state machine)
  ├── repository (investigation_workflows + child tables)
  ├── timeline (workflow activity JSON, extends forensic timeline)
  ├── notifications (in-app only)
  └── audit (immutable AuditEvent records)
```

`WORKFLOW_POLICY_VERSION = 1.0`

## State machine

Statuses:

`NEW → ACTIVE → UNDER_REVIEW → REQUIRES_CHANGES | APPROVED → REPORTED → ARCHIVED`

| From | Allowed next |
| --- | --- |
| NEW | ACTIVE |
| ACTIVE | UNDER_REVIEW, ARCHIVED |
| UNDER_REVIEW | REQUIRES_CHANGES, APPROVED, ACTIVE |
| REQUIRES_CHANGES | ACTIVE, UNDER_REVIEW |
| APPROVED | REPORTED, UNDER_REVIEW |
| REPORTED | ARCHIVED |
| ARCHIVED | _(terminal)_ |

Invalid transitions return **HTTP 409**.

## Task lifecycle

Types: `AI_ANALYSIS`, `FORENSIC_REVIEW`, `REPORT_REVIEW`,
`EVIDENCE_VALIDATION`, `TIMELINE_REVIEW`, `CORRELATION_REVIEW`,
`FUSION_REVIEW`, `GENERAL`

Statuses: `OPEN → ASSIGNED → COMPLETED ↔ REOPENED`, or `CANCELLED`

Actions via `PATCH /workflow-tasks/{id}`: `assign`, `complete`, `reopen`,
`cancel`.

## Review lifecycle

### Evidence

`PENDING | APPROVED | REJECTED | NEEDS_REVIEW`

Tracks reviewer, timestamp, comments, reason, and immutable `history`.

### Report approval

`draft → review → approved → published` (or `revision_required`)

**Reports cannot publish unless approved** (HTTP 409).

## Milestones

- Investigation Started
- Evidence Collection Complete
- AI Analysis Complete
- Fusion Complete
- Correlation Complete
- Timeline Complete
- Report Drafted
- Report Approved
- Case Closed

Completion is auto-derived from persisted evidence/AI/fusion/correlation/
timeline/report/status data when possible.

## Notification model

In-app only (no email/external):

- `assigned_task`
- `review_request`
- `approval_required`
- `workflow_completed`
- `report_published`

## API endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/cases/{id}/investigation-workflow` | Current workflow + activity |
| PATCH | `/cases/{id}/investigation-workflow/status` | Validated status transition |
| GET/POST | `/cases/{id}/workflow-tasks` | List / create tasks |
| PATCH | `/workflow-tasks/{id}` | Assign / complete / reopen / cancel |
| GET/POST | `/cases/{id}/workflow-notes` | List / create notes |
| GET/POST | `/cases/{id}/workflow-reviews` | List / create reviews |
| PATCH | `/workflow-reviews/{id}` | Advance review / publish |
| GET | `/cases/{id}/workflow-milestones` | Milestone timeline |
| GET | `/cases/{id}/workflow-notifications` | Case workflow notifications |

### Spec path mapping

| Spec path | Implemented path | Reason |
| --- | --- | --- |
| `/cases/{id}/workflow` | `/cases/{id}/investigation-workflow` | 8B owns `/workflow` |
| `/cases/{id}/tasks` | `/cases/{id}/workflow-tasks` | 8B owns `/tasks` |
| `/tasks/{id}` | `/workflow-tasks/{id}` | 8B owns `/tasks/{id}` |
| notes / reviews / milestones / notifications | `workflow-*` | Avoid 8B `/reviews` and `/notifications` |

Migration: `20260905_0024_add_workflow.py` (spec cited `20260901_0017`,
already used by reports).

## Audit guarantees

- Every status change, task mutation, note create, review decision, and
  milestone produces an `AuditEvent` with category `investigation_workflow`.
- Review and note histories are append-only JSON.
- Workflow activity is append-only on `investigation_workflows.activity`.
- No silent state changes — transitions go through the engine.

## Frontend

Investigation Workspace **Workflow** tab:

- `WorkflowPanel`, `TaskBoard`, `ReviewPanel`, `MilestoneTimeline`,
  `NotesPanel`, `NotificationsPanel`, `WorkflowStatusBadge`
- Hooks: `useWorkflow.ts`
- API: `services/api/workflow.ts`
- Types: `types/workflow.ts`

Components live under `frontend/src/components/workflow/` and do not replace
Phase 8B collaboration panels.
