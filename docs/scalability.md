# Scalability & High Availability (Phase 10E)

Additive architecture for enterprise-scale AI-Forge deployments.
**No AI algorithm changes. No forensic logic changes.**
Single-node mode (`JOB_QUEUE_MODE=local`) preserves today’s deterministic
BackgroundTasks behavior.

## Package

```
backend/app/scaling/
  workers.py      Configurable worker pools / queues
  queues.py       Local | Redis/Celery queue abstraction
  dispatcher.py   API-facing enqueue façade
  scheduler.py    Coordinated schedule ticks + locks
  balancing.py    LB / sticky-session guidance
  cache.py        Namespaced Redis cache, TTL, locks
  database.py     Pool helpers, read replica URL, retries
  tasks.py        Celery wrappers around existing orchestrators
  storage_factory.py
```

## Worker pools

| Pool | Queue |
| --- | --- |
| extraction | `ai-forge.extraction` |
| ocr | `ai-forge.ocr` |
| image_ai | `ai-forge.image-ai` |
| document_ai | `ai-forge.document-ai` |
| signature_ai | `ai-forge.signature-ai` |
| video_ai | `ai-forge.video-ai` |
| audio_ai | `ai-forge.audio-ai` |
| fusion | `ai-forge.fusion` |
| correlation | `ai-forge.correlation` |
| reporting | `ai-forge.reporting` |
| default | `ai-forge.default` |

Workers execute the **same** `ProcessingOrchestrator.run(job_id)` path used locally.

## Queue modes

| `JOB_QUEUE_MODE` | Behavior |
| --- | --- |
| `local` (default) | FastAPI `BackgroundTasks` — identical to pre-10E |
| `redis` / `celery` | Celery `apply_async` onto pool queues |

Business processors are not rewritten for distribution.

## Redis

- Namespaces: `http`, `ai_meta`, `worker`, `lock`, `coord`
- TTL policies: short 15s / medium 60s / long 300s
- Invalidation helpers + SCAN prefix delete
- Distributed locks for schedule/worker coordination
- Heartbeats under `coord:heartbeat:*`

Do **not** cache forensic findings, scores, or custody records.

## Database

- Existing pool settings remain (`DB_POOL_SIZE`, overflow, timeout, recycle)
- Optional `DATABASE_READ_URL` for read-replica configuration
- `with_db_retry` for transient failures / statement timeout

Size pools against `replicas × (pool_size + max_overflow)`.

## Storage

| `STORAGE_BACKEND` | Adapter |
| --- | --- |
| `local` | `LocalStorage` (default) |
| `s3` / `minio` | `S3CompatibleStorage` (requires boto3) |
| `azure` | Configured adapter (requires azure-storage-blob to operate) |
| `gcs` | Configured adapter (requires google-cloud-storage to operate) |

Evidence APIs and key schemes are unchanged.

For multi-replica APIs with local disks, use RWX volumes **or** object storage.
Sticky sessions are only recommended when affinity to local PVC is unavoidable.

## Load balancing

- Stateless API when object storage is used
- Ingress / reverse proxy can scale backend Service endpoints
- Health: `/api/v1/system/readiness`
- Liveness: `/api/v1/system/liveness`
- Prefer no sticky sessions unless local storage affinity is required

## Kubernetes

Added / updated under `deployment/k8s/`:

- `backend-deployment.yaml` — rolling updates, probes, resources, `JOB_QUEUE_MODE`
- `worker-deployment.yaml` — Celery workers with queue list, probes, resources
- `hpa-pdb.yaml` — HorizontalPodAutoscaler + PodDisruptionBudget for API & worker

## Operations checklist

1. Keep `JOB_QUEUE_MODE=local` for single-node / CI
2. Production: broker (RabbitMQ) + Redis + `JOB_QUEUE_MODE=celery`
3. Prefer object storage for HA evidence
4. Apply HPA/PDB after baseline load testing
5. Monitor queue depth, worker heartbeats, DB connections
