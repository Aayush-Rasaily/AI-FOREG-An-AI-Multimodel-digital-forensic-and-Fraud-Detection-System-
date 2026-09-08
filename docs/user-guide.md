# User guide

Manual for investigators and analysts using the AI-Forge workspace.
This is the public v1.0 user manual. Step-by-step investigation detail
remains in [investigator-guide.md](investigator-guide.md).

AI outputs **assist** professional judgment. They do not replace a qualified
examiner, legal review, or organizational policy.

## Sign in

1. Open the application URL provided by your administrator.
2. Sign in at `/login` with your username and password.
3. Access tokens expire in minutes; the client refreshes them automatically.
4. Sign out when finished. Use remember-me only on a dedicated workstation.

If you land on `/unauthorized`, you lack a required permission. Ask an
administrator to assign a role — do not share accounts.

## Create a case

1. Open **Investigations**.
2. Create a case (title, optional description, priority).
3. Note the server-assigned `case_number` (for example `CASE-000001`).
4. Open the case to reach `/investigations/:caseId`.

## Upload evidence

Use the workspace upload control. Originals are hashed with SHA-256 and stored
read-only. The same hash cannot be registered twice in one case. Only
allow-listed types are accepted. See [evidence-management.md](evidence-management.md).

## Run analyses

Typical order:

1. Process the file (normalization / derived artifacts).
2. Extract localizable content if needed.
3. Run forensic analysis and modality AI (image, document, video, audio,
   signature) as required by the investigation.
4. Wait for job status; unavailable models are reported explicitly.

Guidance: [ai-analysis-guide.md](ai-analysis-guide.md),
[processing-pipeline.md](processing-pipeline.md).

## View AI findings

Open the corresponding workspace panel. Findings are stored results of a
specific run — they are not live re-scores of the original bytes. Treat
confidence values as investigative hints.

## Timeline exploration

Run timeline reconstruction from the case, then inspect events, gaps, and
ordering. Methodology: [timeline-engine.md](timeline-engine.md),
[forensic-methodology.md](forensic-methodology.md).

## Correlation analysis

Run correlation and, if authorized, entity resolution or the knowledge graph.
These products consume stored evidence and prior findings.
See [correlation-engine.md](correlation-engine.md).

## Reports

Generate a report after the products you need exist. Download from **Reports**.
Reports carry provenance of included runs. See [reporting-guide.md](reporting-guide.md).

## Exporting results

Authorized users export packages from **Interoperability**
(`interop.export`). Imports require `interop.import`. Do not export onto
uncontrolled media without your agency’s handling rules.
