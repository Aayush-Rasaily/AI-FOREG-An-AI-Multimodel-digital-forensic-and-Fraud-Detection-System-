# Disaster Recovery & Business Continuity (Phase 10F)

Enterprise backup, integrity verification, restore validation, and retention
tooling for AI-Forge.

**No forensic logic, AI algorithm, or investigation workflow changes.**
Phase 8G deployment backup markers remain supported.

## Package

```
backend/app/recovery/
  backup.py         Stamped backup bundles + SHA-256 manifests
  restore.py        Pre-restore validation + operator restore plan
  retention.py      Configurable retention enforcement
  verification.py   Checksum / version verification
```

Scripts:

```
deployment/scripts/backup.sh
deployment/scripts/restore.sh
deployment/scripts/verify_backup.sh
deployment/scripts/cleanup.sh
```

## Objectives

| Metric | Target |
| --- | --- |
| **RPO** | ≤ 24 hours (daily backups); ≤ 4 hours for critical production with 6-hour cadence |
| **RTO** | ≤ 4 hours for full environment restore with validated dumps; ≤ 1 hour for config/report-only recovery |

Tune schedules to meet contractual RPO/RTO; document actual measured values after drills.

## Backup schedule

Recommended cron (UTC):

```cron
# Daily full operational backup at 02:15
15 2 * * * cd /opt/ai-forge && ENV_FILE=.env.production bash deployment/scripts/backup.sh
# Weekly retention cleanup dry-run report (Mondays)
0 3 * * 1 cd /opt/ai-forge && bash deployment/scripts/cleanup.sh
# Monthly apply retention (first Sunday)
0 4 * * 0 cd /opt/ai-forge && APPLY=YES bash deployment/scripts/cleanup.sh
```

Components captured:

- PostgreSQL dump (when Compose postgres is running)
- Redis RDB snapshot (optional)
- Evidence **metadata** index (binaries via object storage / PVC backup)
- AI + application configuration export
- Uploaded reports and investigation exports under `storage_root`

Every bundle writes `manifest.json` with:

- SHA-256 per file
- creation timestamp
- application version
- schema / migration version (`EXPECTED_MIGRATION_HEAD`)
- backup engine version (`10f.1.0`)

## Restore workflow

1. Identify bundle: `data/deployment/backups/<stamp>/`
2. Verify: `bash deployment/scripts/verify_backup.sh <bundle>`
3. Validate: `bash deployment/scripts/restore.sh <bundle>` (plan only)
4. Maintenance window — stop API/workers writers
5. Apply: `CONFIRM=YES bash deployment/scripts/restore.sh <bundle>`
6. Run migrations if schema requires it
7. Platform readiness + release-check
8. Resume traffic; spot-check a known case/report

Restore is **blocked** if checksum verification fails.

## Retention

| Target | Default days | Setting |
| --- | --- | --- |
| backups | 30 | `BACKUP_RETAIN_DAYS` |
| reports | 90 | `REPORT_RETAIN_DAYS` |
| temporary files | 1 | `TEMP_RETAIN_DAYS` |
| logs | 14 | `LOG_RETAIN_DAYS` |
| exports | 60 | `EXPORT_RETAIN_DAYS` |
| AI cache | 7 | `AI_CACHE_RETAIN_DAYS` |

`cleanup.sh` never deletes evidence originals under `evidence/`.

## Disaster scenarios

### Complete server loss
1. Provision replacement hosts / cluster
2. Restore object storage / PVC evidence separately
3. Restore latest verified DB dump
4. Deploy application release matching `application_version` / schema
5. Verify readiness; restore reports/exports from bundle

### Database corruption
1. Stop writers
2. Verify latest bundle with postgres artifact
3. Restore dump into empty database
4. Re-run migrations only if required
5. Validate sample investigations

### Redis loss
- Treat as ephemeral cache/rate-limit/session accelerator unless Redis persistence is mandated
- Restart Redis; rate limits/cache rebuild automatically
- Restore `redis.rdb` only when intentionally persisted

### Storage failure
1. Fail over to replica bucket / restored PVC
2. Point `STORAGE_BACKEND` / roots at recovered storage
3. Reconcile evidence metadata vs object keys

### Accidental deletion
1. Locate pre-deletion backup stamp
2. Verify + restore affected reports/exports/DB rows
3. Do **not** invent forensic findings — restore only authenticated artifacts

### Rollback after failed deployment
1. Keep prior image tags + previous backup stamp
2. Roll Kubernetes/Compose to last known good
3. If schema migrated forward incompatibly, restore DB from pre-deploy dump
4. Re-run release-check

## Operational runbook

| Step | Action |
| --- | --- |
| Daily | Confirm backup job success + non-empty `manifest.json` |
| Weekly | `verify_backup.sh` on newest stamp; review cleanup dry-run |
| Monthly | Full restore drill in staging; update measured RTO/RPO |
| Incident | Freeze writes → verify backup → restore → readiness → reopen |

## Security notes

- Secrets must come from vault/KMS, not from committed dumps
- Configuration export is sanitized (see `export_configuration`)
- Restrict filesystem ACLs on `data/deployment/backups/`
- Encrypt backup media at rest for off-site copies
