# API Reference

All version-one HTTP endpoints. Base path: `/api/v1`.
Interactive OpenAPI is served at `/docs` when `DEBUG=true`.
This catalog is generated from route decorators in
`backend/app/api/v1/endpoints/` (259 operations).

Related: [authentication.md](authentication.md),
[security-hardening.md](security-hardening.md).

## Conventions

### Envelope

Success:

```json
{
  "success": true,
  "data": {},
  "request_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "timestamp": "2026-09-07T10:00:00+00:00"
}
```

Error:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Client-safe explanation",
    "request_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "details": {}
  },
  "timestamp": "2026-09-07T10:00:00+00:00"
}
```

### Authentication

When `JWT_SECRET` is set, send `Authorization: Bearer <access_token>`.
Public without a token (`PUBLIC_PATHS`):

- `GET /health`, `/health/live`, `/health/ready`
- `GET /metrics`
- `GET /system/liveness`, `/system/readiness`
- `POST /auth/login`, `POST /auth/refresh`

Other `/auth/*` routes require a valid access token. Missing credentials →
`401`. Missing permission → `403`. See [authentication.md](authentication.md).

### Rate limits (Phase 10D defaults)

| Category | Burst | Sustained | Typical paths |
| --- | --- | --- | --- |
| auth | 10 / 60s | 60 / hour | `/auth/*` |
| upload | 20 / 60s | 200 / hour | evidence POST |
| ai | 30 / 60s | 300 / hour | AI/forensics/fusion POST |
| report | 10 / 60s | 100 / hour | report POST |
| search | 60 / 60s | 600 / hour | search/query |
| export | 10 / 60s | 50 / hour | export POST |

Exceeded limits return `429`. Health and metrics are not limited.

### Common status codes

| Code | Meaning |
| --- | --- |
| 200 | Success |
| 201 | Created |
| 202 | Accepted (async job queued) |
| 400 | Validation / business-rule error |
| 401 | Unauthenticated |
| 403 | Authenticated but not permitted |
| 404 | Resource not found |
| 409 | Conflict (duplicate, state) |
| 413 | Upload too large |
| 415 | Unsupported media type |
| 422 | Request body schema error |
| 429 | Rate limited |
| 500 | Unexpected server error |

### Pagination

List endpoints typically accept `limit` (1–100, default 20) and `offset`.
Responses include `items`, `total`, `limit`, and `offset` where applicable.

### Worked examples

Login:

```http
POST /api/v1/auth/login
Content-Type: application/json

{"username": "investigator", "password": "********", "remember_me": false}
```

```json
{
  "success": true,
  "data": {
    "access_token": "<jwt>",
    "refresh_token": "<opaque>",
    "token_type": "bearer"
  }
}
```

Create a case:

```http
POST /api/v1/cases
Authorization: Bearer <access_token>
Content-Type: application/json

{"title": "Wire-transfer dispute", "priority": "high"}
```

Upload evidence (`multipart/form-data` field `file`):

```http
POST /api/v1/cases/{case_id}/evidence
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

Queue processing (async `202`):

```http
POST /api/v1/evidence/{evidence_id}/process
Authorization: Bearer <access_token>
```

## Endpoint catalog

### Admin

| Method | Path | Notes |
| --- | --- | --- |
| `GET` | `/api/v1/roles` | List roles (HTTP 200) |
| `GET` | `/api/v1/permissions` | List permissions (HTTP 200) |
| `GET` | `/api/v1/sessions` | List sessions (HTTP 200) |
| `DELETE` | `/api/v1/sessions/{session_id}` | Revoke one session (HTTP 200) |
| `DELETE` | `/api/v1/sessions` | Revoke all sessions for the current user (HTTP 200) |

### Ai

| Method | Path | Notes |
| --- | --- | --- |
| `GET` | `/api/v1/models` | List registered AI models (HTTP 200) |
| `GET` | `/api/v1/models/{model_id}` | Retrieve one AI model (HTTP 200) |
| `POST` | `/api/v1/models/reload` | Reload one AI model (HTTP 200) |
| `GET` | `/api/v1/inference/jobs` | List inference jobs (HTTP 200) |
| `GET` | `/api/v1/inference/jobs/{job_id}` | Retrieve one inference job (HTTP 200) |

### Analytics

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/analytics/refresh` | analytics (HTTP 200) |
| `GET` | `/api/v1/analytics` | analytics (HTTP 200) |
| `GET` | `/api/v1/analytics/dashboard` | analytics (HTTP 200) |
| `GET` | `/api/v1/analytics/cases` | analytics (HTTP 200) |
| `GET` | `/api/v1/analytics/evidence` | analytics (HTTP 200) |
| `GET` | `/api/v1/analytics/ai` | analytics (HTTP 200) |
| `GET` | `/api/v1/analytics/workflow` | analytics (HTTP 200) |
| `GET` | `/api/v1/analytics/integrity` | analytics (HTTP 200) |
| `GET` | `/api/v1/analytics/export` | analytics (HTTP 200) |

### Audio Ai

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/evidence/{evidence_id}/audio-analysis` | Queue AI audio forensic analysis (HTTP 202) |
| `GET` | `/api/v1/evidence/{evidence_id}/audio-analysis` | List AI audio analysis history (HTTP 200) |
| `GET` | `/api/v1/audio-analysis/{analysis_id}` | Retrieve one AI audio analysis run (HTTP 200) |
| `GET` | `/api/v1/evidence/{evidence_id}/audio-findings` | List AI audio findings (HTTP 200) |
| `GET` | `/api/v1/audio-analysis/{analysis_id}/timeline` | List timeline entries for one analysis run (HTTP 200) |
| `GET` | `/api/v1/audio-analysis/{analysis_id}/segments` | List localized segments for one analysis run (HTTP 200) |
| `GET` | `/api/v1/audio-analysis/{analysis_id}/features` | Retrieve feature summary for one analysis run (HTTP 200) |

### Audit

| Method | Path | Notes |
| --- | --- | --- |
| `GET` | `/api/v1/audit` | List audit events (HTTP 200) |
| `POST` | `/api/v1/audit/verify` | Verify evidence and report integrity (HTTP 200) |
| `GET` | `/api/v1/audit/export` | Export audit log (HTTP 200) |
| `GET` | `/api/v1/audit/{event_id}` | Get one audit event (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/audit` | List audit events for a case (HTTP 200) |
| `GET` | `/api/v1/evidence/{evidence_id}/audit` | List audit events for evidence (HTTP 200) |

### Auth

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/auth/login` | Sign in with username and password (HTTP 200) |
| `POST` | `/api/v1/auth/refresh` | Refresh an access token (HTTP 200) |
| `POST` | `/api/v1/auth/logout` | Sign out of the current session (HTTP 200) |
| `GET` | `/api/v1/auth/me` | Get the current user (HTTP 200) |
| `POST` | `/api/v1/auth/password` | Change the current password (HTTP 200) |

### Case Intelligence

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/cases/{case_id}/intelligence` | Queue case-level forensic intelligence synthesis (HTTP 202) |
| `GET` | `/api/v1/cases/{case_id}/intelligence` | List case intelligence analysis history (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/intelligence/latest` | Retrieve latest case intelligence assessment (HTTP 200) |
| `GET` | `/api/v1/case-intelligence/{analysis_id}` | Retrieve one case intelligence run (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/relationships` | List cross-evidence relationships for latest case run (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/conflicts` | List case-level conflicts for latest run (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/intelligence/timeline` | List case intelligence timeline for latest run (HTTP 200) |

### Case Review

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/cases/{case_id}/case-review` | case review (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/case-review/preview` | case review (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/case-review/latest` | case review (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/case-review` | case review (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/case-review/checklist` | case review (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/case-review/approvals` | case review (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/case-review/metrics` | case review (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/case-review/history` | case review (HTTP 200) |
| `GET` | `/api/v1/case-review/{review_id}` | case review (HTTP 200) |
| `PATCH` | `/api/v1/case-review/checklist/{item_id}` | case review (HTTP 200) |
| `POST` | `/api/v1/case-review/approvals` | case review (HTTP 200) |

### Cases

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/cases` | Create an investigation case (HTTP 201) |
| `GET` | `/api/v1/cases` | List investigation cases (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}` | Retrieve an investigation case (HTTP 200) |
| `PATCH` | `/api/v1/cases/{case_id}` | Update an investigation case (HTTP 200) |

### Collaboration

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/cases/{case_id}/members` | collaboration (HTTP 201) |
| `GET` | `/api/v1/cases/{case_id}/members` | collaboration (HTTP 200) |
| `PATCH` | `/api/v1/cases/{case_id}/members/{member_id}` | collaboration (HTTP 200) |
| `DELETE` | `/api/v1/cases/{case_id}/members/{member_id}` | collaboration (HTTP 201) |
| `POST` | `/api/v1/cases/{case_id}/tasks` | collaboration (HTTP 201) |
| `GET` | `/api/v1/cases/{case_id}/tasks` | collaboration (HTTP 200) |
| `PATCH` | `/api/v1/tasks/{task_id}` | collaboration (HTTP 200) |
| `DELETE` | `/api/v1/tasks/{task_id}` | collaboration (HTTP 201) |
| `POST` | `/api/v1/evidence/{evidence_id}/assign` | collaboration (HTTP 201) |
| `GET` | `/api/v1/evidence/{evidence_id}/assignments` | collaboration (HTTP 201) |
| `POST` | `/api/v1/comments` | collaboration (HTTP 201) |
| `GET` | `/api/v1/comments/{resource_type}/{resource_id}` | collaboration (HTTP 200) |
| `PATCH` | `/api/v1/comments/{comment_id}` | collaboration (HTTP 200) |
| `DELETE` | `/api/v1/comments/{comment_id}` | collaboration (HTTP 201) |
| `POST` | `/api/v1/reviews` | collaboration (HTTP 201) |
| `PATCH` | `/api/v1/reviews/{review_id}` | collaboration (HTTP 200) |
| `GET` | `/api/v1/notifications` | collaboration (HTTP 200) |
| `PATCH` | `/api/v1/notifications/{notification_id}` | collaboration (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/activity` | collaboration (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/workflow` | collaboration (HTTP 200) |
| `PATCH` | `/api/v1/cases/{case_id}/workflow` | collaboration (HTTP 200) |

### Comparison

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/cases/{case_id}/references` | Register trusted reference evidence (HTTP 201) |
| `GET` | `/api/v1/cases/{case_id}/references` | List trusted reference evidence (HTTP 200) |
| `POST` | `/api/v1/evidence/{evidence_id}/compare` | Compare evidence against reference (HTTP 202) |
| `GET` | `/api/v1/evidence/{evidence_id}/comparisons` | List comparison history (HTTP 200) |
| `GET` | `/api/v1/comparisons/{comparison_id}` | Retrieve one comparison run (HTTP 200) |
| `GET` | `/api/v1/evidence/{evidence_id}/differences` | List comparison differences (HTTP 200) |
| `GET` | `/api/v1/evidence/{evidence_id}/comparison-summary` | Retrieve latest comparison summary (HTTP 200) |

### Correlation

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/cases/{case_id}/correlations` | Queue cross-evidence correlation analysis (HTTP 202) |
| `GET` | `/api/v1/cases/{case_id}/correlations` | List correlation analysis history (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/correlations/latest` | Retrieve latest correlation analysis (HTTP 200) |
| `GET` | `/api/v1/evidence/{evidence_id}/correlations` | List correlations involving one evidence item (HTTP 200) |
| `GET` | `/api/v1/correlations/{correlation_id}` | Retrieve one evidence correlation (HTTP 200) |

### Decision Support

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/cases/{case_id}/decision-support` | decision support (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/decision-support/preview` | decision support (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/decision-support/latest` | decision support (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/decision-support` | decision support (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/decision-support/tasks` | decision support (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/decision-support/review-queue` | decision support (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/decision-support/metrics` | decision support (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/decision-support/decisions` | decision support (HTTP 200) |
| `GET` | `/api/v1/decision-support/{run_id}` | decision support (HTTP 200) |
| `PATCH` | `/api/v1/decision-support/tasks/{task_id}` | decision support (HTTP 200) |
| `POST` | `/api/v1/decision-support/decisions` | decision support (HTTP 200) |

### Document Ai

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/evidence/{evidence_id}/document-analysis` | Queue AI document forensic analysis (HTTP 202) |
| `GET` | `/api/v1/evidence/{evidence_id}/document-analysis` | List AI document analysis history (HTTP 200) |
| `GET` | `/api/v1/evidence/{evidence_id}/document-findings` | List AI document findings (HTTP 200) |

### Entities

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/cases/{case_id}/entities` | Queue entity-resolution analysis (HTTP 202) |
| `GET` | `/api/v1/cases/{case_id}/entities` | List entity-resolution analysis history (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/entities/latest` | Retrieve latest entity-resolution analysis (HTTP 200) |
| `GET` | `/api/v1/entities/{entity_id}` | Retrieve one canonical entity (HTTP 200) |
| `GET` | `/api/v1/entities/{entity_id}/graph` | Retrieve neighborhood graph for one entity (HTTP 200) |
| `GET` | `/api/v1/entities/{entity_id}/relationships` | List relationships for one entity (HTTP 200) |

### Evidence

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/cases/{case_id}/evidence` | Register an evidence object (HTTP 201) |
| `GET` | `/api/v1/cases/{case_id}/evidence` | List evidence for a case (HTTP 200) |
| `GET` | `/api/v1/evidence/{evidence_id}` | Retrieve evidence metadata (HTTP 200) |

### Extraction

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/evidence/{evidence_id}/extract` | Queue evidence extraction (HTTP 202) |
| `GET` | `/api/v1/evidence/{evidence_id}/extractions` | List evidence extractions (HTTP 200) |
| `GET` | `/api/v1/evidence/{evidence_id}/extractions/{extraction_id}` | Retrieve one extraction (HTTP 200) |
| `GET` | `/api/v1/evidence/{evidence_id}/regions` | List localized extraction regions (HTTP 200) |
| `GET` | `/api/v1/evidence/{evidence_id}/extraction-artifacts` | List extraction artifacts (HTTP 200) |

### Forensics

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/evidence/{evidence_id}/analyze` | Queue forensic analysis (HTTP 202) |
| `GET` | `/api/v1/evidence/{evidence_id}/analysis` | List forensic analysis history (HTTP 200) |
| `GET` | `/api/v1/analysis/{analysis_id}` | Retrieve one analysis run (HTTP 200) |
| `GET` | `/api/v1/evidence/{evidence_id}/findings` | List forensic findings (HTTP 200) |
| `GET` | `/api/v1/evidence/{evidence_id}/heatmaps` | List forensic visualization artifacts (HTTP 200) |
| `GET` | `/api/v1/evidence/{evidence_id}/analysis-summary` | Retrieve latest analysis summary (HTTP 200) |

### Fusion

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/evidence/{evidence_id}/fusion-analysis` | Queue multimodal fusion analysis (HTTP 202) |
| `GET` | `/api/v1/evidence/{evidence_id}/fusion-analysis` | List multimodal fusion analysis history (HTTP 200) |
| `GET` | `/api/v1/evidence/{evidence_id}/fusion-analysis/latest` | Retrieve latest multimodal fusion assessment (HTTP 200) |
| `GET` | `/api/v1/fusion-analysis/{analysis_id}` | Retrieve one multimodal fusion analysis run (HTTP 200) |
| `GET` | `/api/v1/evidence/{evidence_id}/fusion-jury` | List jury assessments for latest fusion run (HTTP 200) |
| `GET` | `/api/v1/evidence/{evidence_id}/fusion-conflicts` | List conflicts for latest fusion run (HTTP 200) |
| `GET` | `/api/v1/evidence/{evidence_id}/fusion-signals` | Preview normalized fusion signals (HTTP 200) |

### Health

| Method | Path | Notes |
| --- | --- | --- |
| `GET` | `/api/v1/health` | Check application health (HTTP 200) |
| `GET` | `/api/v1/health/live` | Check process liveness (HTTP 200) |
| `GET` | `/api/v1/health/ready` | Check process readiness (HTTP 200) |
| `GET` | `/api/v1/metrics` | Prometheus metrics exposition (HTTP 200) |

### Image Ai

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/evidence/{evidence_id}/image-analysis` | Queue AI image forensic analysis (HTTP 202) |
| `GET` | `/api/v1/evidence/{evidence_id}/image-analysis` | List AI image analysis history (HTTP 200) |
| `GET` | `/api/v1/image-analysis/{analysis_id}` | Retrieve one AI image analysis run (HTTP 200) |
| `GET` | `/api/v1/evidence/{evidence_id}/image-findings` | List AI image findings (HTTP 200) |

### Integrity

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/cases/{case_id}/integrity-check` | integrity (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/integrity/preview` | integrity (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/integrity/latest` | integrity (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/integrity` | integrity (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/integrity/alerts` | integrity (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/integrity/drift` | integrity (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/integrity/history` | integrity (HTTP 200) |
| `GET` | `/api/v1/integrity/{run_id}` | integrity (HTTP 200) |

### Intelligence

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/cases/{case_id}/investigation-summaries` | Generate investigation intelligence summary (HTTP 201) |
| `GET` | `/api/v1/cases/{case_id}/investigation-summaries` | List investigation intelligence summaries (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/investigation-summaries/latest` | Retrieve latest investigation intelligence summary (HTTP 200) |
| `GET` | `/api/v1/investigation-summaries/{summary_id}` | Retrieve a single investigation intelligence summary (HTTP 200) |

### Interoperability

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/cases/{case_id}/export` | interoperability (HTTP 200) |
| `POST` | `/api/v1/cases/import` | interoperability (HTTP 200) |
| `GET` | `/api/v1/exports` | interoperability (HTTP 200) |
| `GET` | `/api/v1/exports/{export_id}` | interoperability (HTTP 200) |
| `GET` | `/api/v1/exports/{export_id}/manifest` | interoperability (HTTP 200) |
| `GET` | `/api/v1/exports/{export_id}/download` | interoperability (HTTP 200) |
| `GET` | `/api/v1/imports` | interoperability (HTTP 200) |
| `GET` | `/api/v1/imports/{import_id}` | interoperability (HTTP 200) |

### Investigation Intelligence

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/cases/{case_id}/investigation-intelligence` | investigation intelligence (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/investigation-preview` | investigation intelligence (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/investigation-intelligence/latest` | investigation intelligence (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/investigation-intelligence` | investigation intelligence (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/hypotheses` | investigation intelligence (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/evidence-gaps` | investigation intelligence (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/recommendations` | investigation intelligence (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/investigation-summary` | investigation intelligence (HTTP 200) |
| `GET` | `/api/v1/investigation-intelligence/{run_id}` | investigation intelligence (HTTP 200) |

### Knowledge Graph

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/cases/{case_id}/knowledge-graph` | knowledge graph (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/knowledge-graph/preview` | knowledge graph (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/knowledge-graph` | knowledge graph (HTTP 200) |
| `GET` | `/api/v1/knowledge-graph/entities` | knowledge graph (HTTP 200) |
| `GET` | `/api/v1/knowledge-graph/relationships` | knowledge graph (HTTP 200) |
| `GET` | `/api/v1/knowledge-graph/search` | knowledge graph (HTTP 200) |
| `GET` | `/api/v1/knowledge-graph/entity/{entity_id}/neighbors` | knowledge graph (HTTP 200) |
| `GET` | `/api/v1/knowledge-graph/entity/{entity_id}` | knowledge graph (HTTP 200) |
| `GET` | `/api/v1/knowledge-graph/{graph_id}` | knowledge graph (HTTP 200) |

### Monitoring

| Method | Path | Notes |
| --- | --- | --- |
| `GET` | `/api/v1/monitoring/dashboard` | Operational monitoring dashboard (HTTP 200) |
| `GET` | `/api/v1/monitoring/system-health` | Platform health assessment (HTTP 200) |
| `GET` | `/api/v1/monitoring/processing` | Processing operational metrics (HTTP 200) |
| `GET` | `/api/v1/monitoring/ai` | AI operational metrics (HTTP 200) |
| `GET` | `/api/v1/monitoring/api` | API usage metrics derived from audit events (HTTP 200) |
| `GET` | `/api/v1/monitoring/activity` | User and investigation activity metrics (HTTP 200) |
| `GET` | `/api/v1/monitoring/bottlenecks` | Processing and detector bottlenecks (HTTP 200) |
| `GET` | `/api/v1/monitoring/audit-summary` | Audit analytics summary (HTTP 201) |
| `POST` | `/api/v1/monitoring/refresh` | Recompute and persist monitoring snapshots (HTTP 201) |

### Platform Validation

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/platform/validate` | platform validation (HTTP 200) |
| `GET` | `/api/v1/platform/validation` | platform validation (HTTP 200) |
| `GET` | `/api/v1/platform/validation/latest` | platform validation (HTTP 200) |
| `GET` | `/api/v1/platform/validation/{run_id}` | platform validation (HTTP 200) |
| `GET` | `/api/v1/platform/readiness` | platform validation (HTTP 200) |
| `GET` | `/api/v1/platform/health/report` | platform validation (HTTP 200) |

### Processing

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/evidence/{evidence_id}/process` | Queue evidence processing (HTTP 202) |
| `GET` | `/api/v1/evidence/{evidence_id}/processing` | List evidence processing jobs (HTTP 200) |
| `GET` | `/api/v1/processing/{job_id}` | Retrieve a processing job (HTTP 200) |
| `GET` | `/api/v1/evidence/{evidence_id}/artifacts` | List derived evidence artifacts (HTTP 200) |

### Reports

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/cases/{case_id}/reports` | Queue forensic investigation report generation (HTTP 202) |
| `GET` | `/api/v1/cases/{case_id}/reports` | List forensic reports for a case (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/reports/latest` | Get latest forensic report for a case (HTTP 200) |
| `GET` | `/api/v1/reports/{report_id}` | Get one forensic report (HTTP 200) |
| `GET` | `/api/v1/reports/{report_id}/status` | Get forensic report generation status (HTTP 200) |
| `GET` | `/api/v1/reports/{report_id}/download` | Download forensic report (HTTP 200) |

### Security

| Method | Path | Notes |
| --- | --- | --- |
| `GET` | `/api/v1/security/roles` | security (HTTP 200) |
| `GET` | `/api/v1/security/permissions` | security (HTTP 200) |
| `GET` | `/api/v1/security/policy` | security (HTTP 200) |
| `GET` | `/api/v1/security/violations` | security (HTTP 200) |
| `POST` | `/api/v1/security/validate` | security (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/access` | security (HTTP 200) |
| `PATCH` | `/api/v1/cases/{case_id}/access` | security (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/compliance` | security (HTTP 200) |

### Signature Ai

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/signature/verify` | Verify a signature pair (HTTP 200) |
| `GET` | `/api/v1/signature/{verification_id}` | Retrieve one signature verification run (HTTP 200) |
| `POST` | `/api/v1/evidence/{evidence_id}/signature-analysis` | Queue signature verification for evidence (HTTP 202) |
| `GET` | `/api/v1/evidence/{evidence_id}/signature-analysis` | List signature verification history (HTTP 200) |

### System

| Method | Path | Notes |
| --- | --- | --- |
| `GET` | `/api/v1/system/info` | Get safe system information (HTTP 200) |

### System Admin

| Method | Path | Notes |
| --- | --- | --- |
| `GET` | `/api/v1/system/health` | Get system health snapshot (HTTP 200) |
| `GET` | `/api/v1/system/metrics` | Get operational metrics (HTTP 200) |
| `GET` | `/api/v1/system/jobs` | Get background job summary (HTTP 200) |
| `GET` | `/api/v1/system/storage` | Get storage utilization (HTTP 200) |
| `GET` | `/api/v1/system/diagnostics` | Get latest diagnostics results (HTTP 200) |
| `POST` | `/api/v1/system/diagnostics/run` | Run system diagnostics (HTTP 200) |

### System Release

| Method | Path | Notes |
| --- | --- | --- |
| `GET` | `/api/v1/system/version` | system release (HTTP 200) |
| `GET` | `/api/v1/system/release` | system release (HTTP 200) |
| `GET` | `/api/v1/system/liveness` | system release (HTTP 200) |
| `GET` | `/api/v1/system/readiness` | system release (HTTP 200) |
| `GET` | `/api/v1/system/startup-validation` | system release (HTTP 200) |
| `GET` | `/api/v1/system/configuration` | system release (HTTP 200) |
| `POST` | `/api/v1/system/validate` | system release (HTTP 200) |
| `POST` | `/api/v1/system/release-check` | system release (HTTP 200) |

### Timeline

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/cases/{case_id}/timeline` | Queue investigation timeline reconstruction (HTTP 202) |
| `GET` | `/api/v1/cases/{case_id}/timeline` | List investigation timeline history (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/timeline/latest` | Retrieve latest investigation timeline (HTTP 200) |
| `GET` | `/api/v1/timeline/{timeline_id}` | Retrieve one investigation timeline (HTTP 200) |
| `GET` | `/api/v1/timeline/{timeline_id}/conflicts` | List timeline conflicts (HTTP 200) |

### Users

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/users` | Create a user (HTTP 201) |
| `GET` | `/api/v1/users` | List users (HTTP 200) |
| `GET` | `/api/v1/users/{user_id}` | Get a user (HTTP 200) |
| `PATCH` | `/api/v1/users/{user_id}` | Update a user (HTTP 200) |
| `DELETE` | `/api/v1/users/{user_id}` | Deactivate a user (HTTP 200) |

### Video Ai

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/api/v1/evidence/{evidence_id}/video-analysis` | Queue AI video forensic analysis (HTTP 202) |
| `GET` | `/api/v1/evidence/{evidence_id}/video-analysis` | List AI video analysis history (HTTP 200) |
| `GET` | `/api/v1/video-analysis/{analysis_id}` | Retrieve one AI video analysis run (HTTP 200) |
| `GET` | `/api/v1/evidence/{evidence_id}/video-findings` | List AI video findings (HTTP 200) |
| `GET` | `/api/v1/video-analysis/{analysis_id}/frames` | List sampled frames for one analysis run (HTTP 200) |
| `GET` | `/api/v1/video-analysis/{analysis_id}/timeline` | List timeline entries for one analysis run (HTTP 200) |

### Workflow

| Method | Path | Notes |
| --- | --- | --- |
| `GET` | `/api/v1/cases/{case_id}/investigation-workflow` | workflow (HTTP 200) |
| `PATCH` | `/api/v1/cases/{case_id}/investigation-workflow/status` | workflow (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/workflow-tasks` | workflow (HTTP 201) |
| `POST` | `/api/v1/cases/{case_id}/workflow-tasks` | workflow (HTTP 201) |
| `PATCH` | `/api/v1/workflow-tasks/{task_id}` | workflow (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/workflow-notes` | workflow (HTTP 201) |
| `POST` | `/api/v1/cases/{case_id}/workflow-notes` | workflow (HTTP 201) |
| `GET` | `/api/v1/cases/{case_id}/workflow-reviews` | workflow (HTTP 201) |
| `POST` | `/api/v1/cases/{case_id}/workflow-reviews` | workflow (HTTP 201) |
| `PATCH` | `/api/v1/workflow-reviews/{review_id}` | workflow (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/workflow-milestones` | workflow (HTTP 200) |
| `GET` | `/api/v1/cases/{case_id}/workflow-notifications` | workflow (HTTP 200) |

## Live schema

When debugging locally with `DEBUG=true`:

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`

CI validates the generated OpenAPI 3.x document on every pull request
([release-engineering.md](release-engineering.md)).
