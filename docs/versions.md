# Engine and policy versions

Canonical identifiers for AI-Forge **v1.0.0**. Schema head remains
`20260915_0034`.

| Domain | Constant | Typical value |
| --- | --- | --- |
| Application | `APP_VERSION` / `pyproject.toml` | `1.0.0` |
| Deployment engine | `DEPLOYMENT_ENGINE_VERSION` | `8g.1.0` |
| Deployment policy | `DEPLOYMENT_POLICY_VERSION` | `1.0` |
| Reporting | `ENGINE_VERSION` / `REPORT_VERSION` | `1.0` |
| Workflow | `WORKFLOW_POLICY_VERSION` | see `backend/app/workflow/policy.py` |
| Security governance | `SECURITY_POLICY_VERSION` | see `backend/app/security/policy.py` |
| Monitoring | `POLICY_VERSION` | see `backend/app/monitoring/policy.py` |
| Audit | `POLICY_VERSION` | see `backend/app/audit/policy.py` |
| Interop | `INTEROP_ENGINE_VERSION` | see `backend/app/interoperability/policy.py` |
| Backup | `BACKUP_ENGINE_VERSION` | `10f.1.0` |
| CI/CD helpers | `RELEASE_ENGINE_VERSION` | `10g.1.0` |

RC3/RC4 do not bump engine constants. Security review:
[security-rc3.md](security-rc3.md).

Runtime aggregation: `GET /api/v1/system/release` (`docs/release.md`).
