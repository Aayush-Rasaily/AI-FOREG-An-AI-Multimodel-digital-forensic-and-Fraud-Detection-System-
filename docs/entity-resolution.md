"""Entity resolution architecture and policy (Phase 7C)."""

# Architecture

Phase 7C builds a deterministic **investigation graph** from existing Phase 1–7B
outputs. It does **not** run OCR, metadata extraction, or any AI model.

```
existing artifacts
  → normalize identity keys
  → merge into canonical entities
  → emit typed relationships
  → assign ENTITY-###### IDs
  → persist run + graph
```

Package: `backend/app/entities/`

| Module | Role |
|--------|------|
| `normalizer.py` | Deterministic key normalization + OCR regex reuse |
| `resolver.py` | Collect → merge → relate |
| `graph.py` | Ordered nodes/edges serialization |
| `confidence.py` | Fixed confidence policy |
| `provenance.py` | Traceable support payloads |
| `service.py` | Queue/run lifecycle |
| `repository.py` | Persistence queries |

# Supported entity types

Person, Organization, Email, Phone, Address, Website, Domain, Device, Camera,
Vehicle, Bank Account, Crypto Wallet, Document, Image, Video, Audio, QR Code,
Logo, Signature, Location, IP Address, File Hash.

# Merge rules (no ML / LLM / embeddings)

| Key | Entity |
|-----|--------|
| SHA-256 | File Hash |
| normalized email | Email |
| normalized phone | Phone |
| QR payload | QR Code |
| EXIF camera | Camera |
| device model | Device |
| GPS lat/lon | Location |
| domain / URL | Domain / Website |
| IP literal | IP Address |
| wallet / account patterns | Crypto Wallet / Bank Account |
| document identifiers | Document |
| signature match run | Signature |
| face region | Person |
| creator/author metadata | Organization |

Identical normalized keys merge into **one** canonical entity with multi-evidence
support counts.

# Relationship types

owns, uses, created, contains, references, sent_to, received_from, captured_by,
signed_by, located_at, related_to, derived_from, duplicate_of, supports,
contradicts.

Examples:

- media `derived_from` file_hash
- media `contains` email/phone/QR/logo
- media `captured_by` camera
- media `located_at` location
- correlation `same_hash` → media `duplicate_of` media

# Canonical IDs

Stable ordering by `(entity_type, normalized_key, min_evidence_id)` then:

`ENTITY-000001`, `ENTITY-000002`, …

# Provenance

Every entity and edge stores:

- evidence IDs
- extraction IDs
- AI finding IDs
- correlation IDs
- timeline event IDs
- fusion run IDs
- metadata field names
- policy/engine versions

Nothing is persisted without provenance.

# Determinism

- Fixed confidence table in `policy.py` / `confidence.py`
- Canonical entity keys and relationship keys
- Sorted graph serialization
- One active run per case (`QUEUED`/`RUNNING` unique)

# Limitations

- No new NER / person identity beyond face-region or creator metadata
- Vehicle entities only when metadata already contains vehicle fields
- Soft semantic similarity is never used
- Does not replace Phase 6G case intelligence or Phase 7B correlations

# API

- `POST /cases/{case_id}/entities`
- `GET /cases/{case_id}/entities`
- `GET /cases/{case_id}/entities/latest`
- `GET /entities/{id}`
- `GET /entities/{id}/graph`
- `GET /entities/{id}/relationships`
