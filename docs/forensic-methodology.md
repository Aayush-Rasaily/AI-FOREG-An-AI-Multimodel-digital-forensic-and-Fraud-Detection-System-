# Forensic methodology

How AI-Forge treats digital evidence. This document describes **platform
behavior**, not a substitute for agency SOP, ISO/IEC 27037, or expert
testimony.

AI findings, fusion scores, and reconstructed timelines **assist**
investigators. They do not replace professional judgment or establish legal
conclusions by themselves.

## Evidence preservation

- Original bytes are stored read-only after ingest.
- SHA-256 of the original is recorded at registration.
- Derived artifacts (previews, extracts, reports) are separate objects with
  their own hashes.
- Processing never overwrites the original path.

See [evidence-management.md](evidence-management.md) and
[evidence-integrity.md](evidence-integrity.md).

## Chain of custody

Uploads, processing jobs, analysis runs, access grants, and report
generation are audit-relevant events. Correlation identifiers (`X-Request-ID`)
tie HTTP actions to structured logs. Custody is intact only if operators
also protect storage, backups, and administrative access.

## AI analysis workflow

1. Register evidence (hash, type allow-list, size cap).
2. Optional processing and extraction.
3. Optional classic forensics and modality engines (image, document, video,
   audio, signature).
4. Each run is a queued job with stored findings; engines are not silently
   re-invoked inside later stages.

Missing models or runtimes are reported as unavailable.

## Fusion methodology

The multimodal jury consumes **already stored** findings. It does not
re-decode original media. Conflicts and assessments are recorded for the
investigator. See [fusion-ai.md](fusion-ai.md).

## Correlation methodology

Correlation links events and artifacts that already exist on the case. It
does not invent communications or identities that were never extracted.
See [correlation-engine.md](correlation-engine.md).

## Timeline reconstruction

The timeline engine orders stored temporal facts. Gaps are visible; the
engine does not interpolate missing real-world events.
See [timeline-engine.md](timeline-engine.md).

## Validation policy

Platform validation and integrity checks confirm configuration, hashes, and
operational health. They do not certify that a specific exhibit would be
admissible in a given jurisdiction.

## Provenance tracking

Reports include which runs and artifacts were aggregated. Export packages
follow interoperability hashing rules. Reviewers should verify hashes against
the case record before relying on an exported bundle.
