# Architecture overview

AI-Forge is a multimodal digital-forensics and fraud-intelligence platform.
The backend is a **Clean Architecture** FastAPI service. The frontend is a
Vite/React investigation workspace. Workers, object storage, PostgreSQL, Redis,
and RabbitMQ sit outside the request process.

Phase-specific deep dives remain in the original docs (for example
[processing-pipeline.md](processing-pipeline.md),
[fusion-ai.md](fusion-ai.md)). This page is the enterprise map.

## Clean Architecture

```text
HTTP (api/)  ──┐
               ├──► application/ (use cases) ──► domain/ (ports & types)
Celery/infra ──┘
```

| Layer | Location | May depend on |
| --- | --- | --- |
| Domain | `backend/app/domain/` | Nothing framework-specific |
| Application | `backend/app/application/` | Domain ports |
| Infrastructure | `backend/app/infrastructure/` | Domain + vendors |
| API | `backend/app/api/` | Application services |
| AI engines | `backend/app/ai/`, modality packages | Registry + domain contracts |

Dependencies point **inward**. New detectors register; they do not rewrite
orchestration.

## System architecture

```mermaid
flowchart LR
  investigator[Investigator browser]
  nginx[Nginx TLS reverse proxy]
  spa[Frontend static SPA]
  api[FastAPI API replicas]
  workers[Celery / local job workers]
  pg[(PostgreSQL)]
  redis[(Redis cache)]
  mq[RabbitMQ]
  store[(Object / local storage)]
  models[AI model registry]

  investigator --> nginx
  nginx --> spa
  nginx --> api
  api --> pg
  api --> redis
  api --> store
  api --> workers
  workers --> mq
  workers --> pg
  workers --> store
  workers --> models
```

## Request lifecycle

```mermaid
sequenceDiagram
  actor User
  participant SPA as React SPA
  participant API as FastAPI
  participant Auth as JWT / RBAC
  participant App as Application service
  participant DB as PostgreSQL
  participant Jobs as Job dispatcher

  User->>SPA: Sign in / open case
  SPA->>API: HTTPS + Bearer token
  API->>Auth: Authenticate + permission map
  alt Denied
    Auth-->>SPA: 401 / 403
  else Allowed
    API->>App: Use case
    App->>DB: Read/write metadata
    opt Long running
      App->>Jobs: Queue job (202)
      Jobs-->>DB: Persist run status
    end
    App-->>SPA: ApiResponse envelope
  end
```

## Processing pipeline

Original bytes are **read-only**. Processing writes independently hashed
artifacts. Analysis never mutates the original object.

```mermaid
flowchart TD
  upload[Evidence upload] --> hash[SHA-256 + MIME classify]
  hash --> store[Store original]
  store --> custody[Chain of custody event]
  custody --> process[Processing job]
  process --> extract[Extraction / OCR / regions]
  extract --> forensics[Forensic + modality AI]
  forensics --> fusion[Multimodal fusion / jury]
  fusion --> corr[Correlation + entities + timeline]
  corr --> report[Report engine]
```

See [processing-pipeline.md](processing-pipeline.md) and
[backend-architecture.md](backend-architecture.md).

## AI orchestration

Models register in `ModelRegistry`. Inference jobs persist separately from
forensic findings. Modality analyzers (image, document, signature, video,
audio) and the fusion jury **consume stored findings**; they do not silently
re-run each other.

Details: [ai-architecture.md](ai-architecture.md),
[ai-model-infrastructure.md](ai-model-infrastructure.md).

## Multimodal fusion

Phase 6F normalizes findings, scores six deterministic jury roles, records
conflicts, and stores a fusion assessment. Unavailable modalities are not
treated as negative proof.

## Correlation engine

Case-scoped correlation links evidence items using persisted metadata and
findings. Entity resolution and the knowledge graph are adjacent, additive
read models.

## Reporting engine

The report generator **aggregates** existing snapshots (no new AI). Output
formats include JSON, Markdown, HTML, and downloadable artifacts with
provenance checksums.

## Deployment topology

```mermaid
flowchart TB
  subgraph edge [Edge]
    tls[TLS / Nginx]
  end
  subgraph compute [Compute]
    fe[Frontend Deployment]
    be[API Deployment + HPA]
    wk[Worker Deployment]
  end
  subgraph data [Data]
    pg[(PostgreSQL)]
    rd[(Redis)]
    rq[RabbitMQ]
    obj[(S3 / Azure / GCS / local)]
  end
  tls --> fe
  tls --> be
  be --> pg
  be --> rd
  be --> obj
  wk --> rq
  wk --> pg
  wk --> obj
```

See [deployment-guide.md](deployment-guide.md) and
[scalability.md](scalability.md).

## Investigation workflow

```mermaid
flowchart LR
  A[Create case] --> B[Upload evidence]
  B --> C[Process + extract]
  C --> D[Run AI / forensics]
  D --> E[Fusion]
  E --> F[Correlate / timeline / entities]
  F --> G[Review + collaborate]
  G --> H[Generate report]
  H --> I[Export / retain]
```

User steps: [investigator-guide.md](investigator-guide.md).
