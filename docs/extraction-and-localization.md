# Phase 5A: Extraction and Localization

Phase 5A converts verified, processed evidence into structured, traceable
records. It stops at extraction:

```text
Evidence -> Processing -> Extraction -> Structured Evidence -> Regions
```

It does not decide whether an image, document, voice, face, logo, signature,
or frame is authentic or fraudulent. ELA, manipulation detection, deepfake
detection, fraud scores, AI Jury, and report generation remain out of scope.

## Architecture

`ExtractionService` owns job creation, repeatability, custody events, artifact
creation, and record persistence. It selects an `EvidenceExtractor` by source
capability; API routes do not know parser implementation details.

```python
class EvidenceExtractor(Protocol):
    def can_extract(self, context: ExtractionContext) -> bool: ...
    async def extract(self, context: ExtractionContext) -> ExtractionResult: ...
```

Current adapters are:

- `ImageExtractor`: Pillow dimensions, format, mode, and an empty region
  manifest. Optional Tesseract OCR can add provider-backed word boxes.
- `DocumentExtractor`: native PDF page dimensions and text using pypdf.
- `AudioExtractor`: WAV metadata with the Python standard library; other
  formats use optional `ffprobe`.
- `VideoExtractor`: optional `ffprobe` metadata. Frame sampling is bounded by
  configuration and remains explicitly unavailable until a safe ffmpeg
  executable is installed.

## Provenance and coordinates

Every `ExtractionRecord` contains `evidence_id`, source type and identifier,
extraction type, method, version, and applicable page, frame, timestamp,
confidence, content, and artifact reference. The source identifier is the
original evidence filename or a future derived-artifact identifier; filesystem
paths are never returned by the API.

`BoundingBox` uses a top-left origin:

- `x` increases to the right.
- `y` increases downward.
- `width` and `height` extend right and downward.

Absolute coordinates use the source image/document units. Normalized
coordinates are floats from `0.0` to `1.0`, bounded to the source. PDF native
text currently has no coordinates from pypdf, so its location is `null` rather
than fabricated.

## OCR

`OCRProvider` is a replaceable interface with text, word, and line operations.
The initial provider is `TesseractOCRProvider`, backed by the `pytesseract`
adapter and an explicitly installed `tesseract` executable. OCR is disabled by
default. Enabling it does not download models. If the executable is absent,
the image extraction remains intact and reports `PARTIAL` with
`OCR_UNAVAILABLE`.

Raw extracted values are preserved. Conservative number and date patterns
store the raw value and, for safely parseable dates, a separate normalized
value. No semantic meaning is assigned to a number.

## Artifacts and repeatability

Large structured output is stored through the Phase 4 `ArtifactService`, never
in the extraction-record binary fields. Extraction artifact types include
`DOCUMENT_STRUCTURE`, `TEXT_RESULT`, `OCR_RESULT`, `IMAGE_REGIONS`,
`VIDEO_FRAME_INDEX`, and `AUDIO_STREAM_INFO`. Each artifact has its own
storage key, byte size, and SHA-256 hash.

Extraction uses the existing `ProcessingJob` table with job type `EXTRACTION`.
The source SHA-256 and extractor version are recorded in job metadata. A
repeat for unchanged evidence and the same version returns the existing job
instead of creating duplicate records. Failed jobs can be retried; a
capability-unavailable result remains explicit and idempotent until the
extractor version or configuration is changed.

Lifecycle custody events are `EXTRACTION_STARTED`, `EXTRACTION_COMPLETED`,
`EXTRACTION_FAILED`, and `EXTRACTION_ARTIFACT_CREATED`. Events contain safe
operation metadata and never extracted sensitive content.

## API

- `POST /api/v1/evidence/{evidence_id}/extract`
- `GET /api/v1/evidence/{evidence_id}/extractions`
- `GET /api/v1/evidence/{evidence_id}/extractions/{extraction_id}`
- `GET /api/v1/evidence/{evidence_id}/regions`
- `GET /api/v1/evidence/{evidence_id}/extraction-artifacts`

All responses use the existing API envelope and bounded pagination. Extraction
content is rendered as text, not HTML. No filesystem paths are exposed.

## Configuration and limitations

Extraction limits include maximum pages, text characters, record count, frame
sampling interval, and maximum sampled frames. The original storage key is
read-only and is re-verified before queuing extraction.

Pillow, pypdf, and pytesseract are lightweight Python dependencies. Tesseract,
ffprobe, and ffmpeg are external capabilities and are not bundled. In the
current Windows development environment, those executables are not installed:
WAV extraction works through the standard library, while unsupported audio and
video capabilities return explicit unavailable states. No fake frames,
coordinates, OCR values, face regions, signature regions, or logo regions are
created.

The frontend extraction panel shows status, text, page/frame provenance,
confidence, artifacts, and neutral localization overlays when normalized boxes
exist. It does not display fraud or authenticity labels.

Future forensic detectors may implement the same extractor/record contracts
and populate region types, but that integration belongs to later phases.
