# Manual UAT checklist — AI-Forge v1.0.0

Structured acceptance tests. Record pass/fail on a copy of this page.
Do not use real evidence.

## Digital forensic investigator

- [ ] Sign in; session refresh works; sign out revokes access
- [ ] Create a case; `case_number` is assigned
- [ ] Upload allow-listed evidence; SHA-256 shown; original is not editable
- [ ] Duplicate hash in the same case is rejected
- [ ] Process and extract complete or report unavailable explicitly
- [ ] Image/document/video/audio/signature panels show stored runs only
- [ ] Timeline and correlation consume existing data
- [ ] Report generates and downloads with provenance

## Fraud analyst

- [ ] Fusion/jury does not re-analyze original bytes
- [ ] Conflicts and confidence are visible and not presented as legal findings
- [ ] Comments/tasks work without changing hashes

## Case administrator

- [ ] Members and case access can be granted/revoked as documented
- [ ] Workflow transitions match policy
- [ ] Unauthorized roles receive `/unauthorized` or HTTP 403

## System administrator

- [ ] Users and roles can be managed (`admin.manage_users`)
- [ ] Monitoring and release-check succeed
- [ ] Backup script produces a verifiable bundle on a non-prod copy
