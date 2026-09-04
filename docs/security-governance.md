# Security, Compliance & Governance (Phase 8F)

Phase 8F adds an enterprise governance layer for AI-Forge: deterministic
RBAC catalog, case access control, policy enforcement, compliance reporting,
and forensic chain validation.

It is **strictly additive**. Platform authentication (`roles` /
`permissions` / `PermissionCode`) remains the runtime API gate. Phase 8F
persists a parallel **governance catalog** in `security_roles` /
`security_permissions` and does not replace Phase 8A auth or Phase 8B
`case_members`.

`SECURITY_POLICY_VERSION = 1.0`

## Architecture

```
SecurityService
  ├── rbac / permissions (governance role × permission matrix)
  ├── engine (policy document, compliance, chain validation)
  ├── repository (security_* + case facts)
  ├── compliance (summary serialization)
  └── audit (immutable AuditEvent category=security_governance)
```

## RBAC (governance catalog)

Roles: `ADMIN`, `FORENSIC_ADMIN`, `INVESTIGATOR`, `FORENSIC_ANALYST`,
`REVIEWER`, `AUDITOR`, `READ_ONLY`

Permission resources: Cases, Evidence, AI Analysis, Fusion, Correlation,
Timeline, Reports, Workflow, Monitoring, Administration

Evidence-specific codes include `evidence.export`, `evidence.modify`,
`evidence.review`, `evidence.approve`.

Runtime API authorization continues through existing middleware +
`PermissionCode` (including new `security.view` / `security.manage`).

## Case access

Access levels:

- Owner
- Assigned investigators
- Read-only reviewers
- Auditors
- Administrators

Stored in `case_access_records` (additive to `case_members`). Unauthorized
access returns **HTTP 403**.

## Governance policies

| Policy | Rule |
| --- | --- |
| Case retention | 2555 days |
| Evidence retention | 2555 days |
| Report publication | Requires approval |
| Workflow approval | Archive expects report approval when reports exist |
| AI execution | Requires case access grant |
| Export | Requires `audit.view` capability |

## Compliance reporting

Deterministic summaries cover:

- Chain-of-custody completeness
- Evidence integrity (hashes)
- Audit completeness
- Workflow compliance
- Report approval compliance
- Missing approvals / provenance
- Open policy violations

Statuses: `COMPLIANT` | `PARTIAL` | `NON_COMPLIANT`

## Chain validation

`POST /security/validate` checks:

- Evidence hashes
- Audit continuity
- Timeline continuity
- Workflow continuity
- Report / fusion / correlation provenance

## API

| Method | Path |
| --- | --- |
| GET | `/security/roles` |
| GET | `/security/permissions` |
| GET | `/security/policy` |
| GET | `/security/violations` |
| POST | `/security/validate` |
| GET/PATCH | `/cases/{id}/access` |
| GET | `/cases/{id}/compliance` |

Migration: `20260906_0025_add_security.py` (spec cited `20260901_0018`,
already used by the audit framework).

## Audit guarantees

- Access grants, compliance generation, and validation emit immutable
  `AuditEvent` records (`category=security_governance`).
- Policy violations are append-only until explicitly resolved.
- Compliance reports are persisted snapshots.

## Frontend

- Investigation Workspace **Security** tab: access, compliance, violations
- Administration: `/security` page + Settings link + sidebar entry
- Components under `frontend/src/components/security/`

## Relationship to prior phases

| Phase | Relationship |
| --- | --- |
| 8A Auth | Runtime JWT/RBAC unchanged; 8F adds governance catalog |
| 8B Collaboration | `case_members` unchanged; `case_access_records` is ledger |
| 8D Monitoring | Separate operational KPIs |
| 8E Workflow | Workflow continuity included in chain validation |
