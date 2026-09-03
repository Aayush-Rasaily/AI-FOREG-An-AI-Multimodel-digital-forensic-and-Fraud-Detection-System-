# Collaboration & Investigation Workflow (Phase 8B)

Phase 8B adds multi-user case collaboration on top of Phase 8A RBAC.
It does not modify forensic, AI, fusion, timeline, correlation, entity,
reporting, audit, or monitoring engines.

## Collaboration model

| Entity | Purpose |
| --- | --- |
| `case_members` | Case-scoped roles (owner, lead, investigator, analyst, reviewer, viewer) |
| `evidence_assignments` | Assign evidence work with priority/due date/status |
| `investigation_comments` | Threaded markdown comments with soft delete and edit history |
| `investigation_mentions` | `@username` mention targets |
| `investigation_tasks` | Task board items linked to evidence/reports |
| `investigation_reviews` | Approval workflow for reports, fusion, entities, timelines, closure |
| `notifications` | In-app unread/read/archived notifications |
| `activity_log` | Collaborative feed (separate from Phase 7E audit) |
| `case_workflow_states` | Deterministic case lifecycle stage |

## Workflow lifecycle

```
Open → Evidence Collection → Analysis → Review → Reporting → Closed → Archived
```

Transitions are permission-controlled (`workflow.transition`) and validated
against an allow-list. Invalid transitions return `INVALID_WORKFLOW_TRANSITION`.

## Permissions

| Permission | Typical use |
| --- | --- |
| `collab.manage_members` | Invite/remove/change members, transfer ownership |
| `collab.assign` | Assign evidence |
| `comment.create` / `comment.view` | Comments |
| `task.manage` | Create/update/delete tasks |
| `review.decide` | Request and decide reviews |
| `workflow.transition` | Advance case workflow |

Case owners and lead investigators may manage members even when not platform admins.

## Review process

1. Create review (`state=under_review`)
2. Reviewer decides: `approve` → `approved`, `request_changes` → `changes_requested`, `reject` → `rejected`
3. Notifications are sent to the requester
4. Activity feed records the decision

## Notifications

Kinds: assignment, mention, approval_request, review_completed,
report_generated, case_invitation, task_completed, task_overdue.

Statuses: unread, read, archived. No email/SMS in Phase 8B.

## Assignment model

Evidence assignments store assignee, assigned_by, priority, due date,
status (`pending|in_progress|completed|blocked`), and notes.

## Activity vs audit

`activity_log` captures collaborative UX events for the investigation feed.
Phase 7E `audit_events` remains the immutable forensic/compliance trail and
is not duplicated for every chatty collaboration action.
