# Reporting guide

Investigation reports compile **existing** case products. They do not run new
AI. Engine details: [reporting.md](reporting.md),
[forensic-reporting.md](forensic-reporting.md).

## Generate

In the case workspace or **Reports** page, queue generation:

`POST /api/v1/cases/{case_id}/reports` → `202`

Poll:

- `GET /api/v1/cases/{case_id}/reports`
- `GET /api/v1/cases/{case_id}/reports/latest`
- `GET /api/v1/reports/{report_id}/status`

Permission: `report.generate` to create, `report.view` to list, `report.download`
to fetch bytes.

## Download and formats

`GET /api/v1/reports/{report_id}/download` returns the stored artifact.
Renderers support JSON, Markdown, and HTML with provenance checksums. The
report is a snapshot: later analysis does not silently mutate an issued
report.

## Typical contents

Sections include case summary, evidence inventory, extraction/OCR status,
forensic findings, fusion/jury, correlation, entities, timeline, custody, and
provenance. Missing upstream products appear as absent/unavailable — not as
cleared risk.

## Review and approval

Human review uses case-review and workflow panels (`report.approve` where
granted). Do not treat a generated PDF as a court conclusion without your
organization’s review process.

## Exports

Case packages: `POST /api/v1/cases/{case_id}/export` then
`GET /api/v1/exports/{id}/download`. Import is `POST /api/v1/cases/import`.
Export traffic is rate-limited. See interoperability UI `/interoperability`.
