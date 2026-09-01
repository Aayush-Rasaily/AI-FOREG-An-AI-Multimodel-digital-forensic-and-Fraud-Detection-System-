# Video AI Forensics (Phase 6D)

## Overview

Phase 6D adds an AI-powered video forensic layer that analyzes video evidence using bounded frame sampling, temporal localization, and pluggable detectors. The system produces individual evidence-based findings — never a single "fake video" verdict.

## Architecture

```
Evidence → Integrity → Metadata → Frame Sampling → Face/Region → Detectors → Findings → Artifacts
```

Module: `backend/app/ai/video/`

| Component | Purpose |
|-----------|---------|
| `engine.py` | Orchestrates enabled detectors |
| `service.py` | Job queue, persistence, API mapping |
| `registry.py` | Detector plugin registry |
| `pipelines/video_pipeline.py` | Frame sampling and artifact generation |
| `preprocessing/frames.py` | Deterministic frame IDs and bounded ffmpeg extraction |
| `localization/` | Temporal and frame-level localization |
| `detectors/` | Seven pluggable detectors |

## Detectors

| Detector | Method | Notes |
|----------|--------|-------|
| `deepfake` | AI | Returns `unavailable` when `VIDEO_DEEPFAKE_MODEL_*` not configured |
| `synthetic_video` | AI | Returns `unavailable` when `VIDEO_SYNTHETIC_MODEL_*` not configured |
| `temporal` | classical | Timestamp continuity analysis |
| `frame_manipulation` | classical | Perceptual hash duplication (requires decoded frames) |
| `face_consistency` | classical | Face tracking across frames |
| `compression` | classical | Codec metadata observations |
| `metadata` | classical | Container/encoder metadata from Phase 5 extraction |

## Frame Sampling

Uses Phase 5A bounded sampling (`sample_timestamps`, `bounded_frame_numbers`) and `VIDEO_FRAME_INDEX` artifacts. Every sampled frame includes:

- `frame_index`, `frame_number`, `timestamp_ms`, `timestamp_seconds`
- Deterministic `frame_id` = SHA-256(`source_hash:frame_index:timestamp_ms`)

## Model Configuration

```env
VIDEO_DEEPFAKE_MODEL_ENABLED=true
VIDEO_DEEPFAKE_MODEL_PATH=/path/to/deepfake.pt
VIDEO_DEEPFAKE_MODEL_SHA256=<expected-hash>
VIDEO_DEEPFAKE_MODEL_VERSION=1.0.0

VIDEO_SYNTHETIC_MODEL_ENABLED=true
VIDEO_SYNTHETIC_MODEL_PATH=/path/to/synthetic.pt
VIDEO_SYNTHETIC_MODEL_SHA256=<expected-hash>
VIDEO_SYNTHETIC_MODEL_VERSION=1.0.0
```

Model weights are verified via SHA-256 before load. Mismatch → model not loaded.

## APIs

- `POST /api/v1/evidence/{id}/video-analysis`
- `GET /api/v1/evidence/{id}/video-analysis`
- `GET /api/v1/video-analysis/{analysis_id}`
- `GET /api/v1/evidence/{id}/video-findings`
- `GET /api/v1/video-analysis/{analysis_id}/frames`
- `GET /api/v1/video-analysis/{analysis_id}/timeline`

## Artifacts

Stored separately from originals:

- `AI_VIDEO_FRAME`, `AI_VIDEO_TIMELINE`, `AI_VIDEO_HEATMAP`, `AI_VIDEO_MASK`, `AI_VIDEO_OVERLAY`, `AI_VIDEO_PREDICTION`

## Confidence Policy

- AI detectors: confidence only when a real model runs
- Classical: algorithmic confidence with documented limitations
- Unavailable: `confidence = null`, `status = unavailable`

## Limitations

- Frame decoding requires ffmpeg on the host; without it, metadata-only analysis runs
- Scene cuts and static segments can resemble manipulation signals
- Deepfake/synthetic models are architecture-ready but unavailable until weights are configured
- No fraud scoring, jury, or multimodal fusion (future phases)

## Future Integration

Replace heuristic backends by registering ONNX/PyTorch models through the Phase 6A model registry without changing the detector interface.
