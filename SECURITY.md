# Security Policy

AI-Forge v1.0.0 includes JWT authentication, RBAC, upload allow-lists, audit
logging, and production secret validation. Treat it as **sensitive
investigative software**: do not put real case data in public issues.

## Supported versions

| Version | Support |
| --- | --- |
| 1.0.x | Security fixes for the current stable line |
| &lt; 1.0 | Unsupported (pre-release trains) |

## Reporting a vulnerability

Do **not** open a public GitHub issue for a security defect.

1. Use GitHub **Privately report a vulnerability** on this repository, or
   email the maintainer listed in the repository profile.
2. Include affected version, a minimal reproduction **without** real evidence
   or credentials, and impact.
3. Allow a reasonable window for a patch before public discussion.

We will acknowledge reports and ship a patch release (`1.0.x`) when a fix is
verified. Critical CI scans (`pip-audit`, `npm audit`, Trivy, Gitleaks) fail
the pipeline on **critical** findings.

See [docs/security-rc3.md](docs/security-rc3.md) and
[docs/security-hardening.md](docs/security-hardening.md).
