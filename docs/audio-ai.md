# Audio AI Forensics (Phase 6E)

Phase 6E adds a plugin-oriented **Audio AI Forensics** subsystem under `backend/app/ai/audio/`. It analyzes audio evidence using deterministic classical detectors and optional AI model plugins. Unavailable capabilities return explicit `unavailable` status with `confidence=null`.

## Architecture

```
backend/app/ai/audio/
├── bootstrap.py          # Registry + engine wiring
├── config.py             # AudioAISettings (env-driven model config)
├── engine.py             # Orchestrates enabled detectors
├── registry.py           # Detector plugin registry
├── service.py            # Job queue, persistence, API mapping
├── repository.py         # DB queries
├── schemas.py            # Pydantic API schemas
├── models.py             # Domain types (context, findings, results)
├── preprocessing/audio.py
├── pipelines/audio_pipeline.py
├── detectors/            # Classical + AI detector plugins
├── features/             # MFCC, spectral, waveform helpers
├── localization/timeline.py
└── postprocessing/       # Finding normalization + timeline aggregation
```

The subsystem mirrors Phase 6D (Video AI): registry → engine → service → API, with `ProcessingJobType.AUDIO_AI_ANALYSIS` background execution.

## Supported Formats

| Format | Decode path |
|--------|-------------|
| WAV | Python `wave` (stdlib) |
| MP3, M4A/AAC, FLAC, OGG/Opus | `ffmpeg` when available |

When `ffmpeg` is unavailable, non-WAV formats decode as unavailable. The system never fabricates decoded audio.

## Detectors

| Detector ID | Type | Description |
|-------------|------|-------------|
| `synthetic_audio` | AI | AI-generated speech (model optional) |
| `voice_clone` | AI | Voice cloning indicators (model optional) |
| `deepfake_voice` | AI | Deepfake voice indicators (model optional) |
| `speaker_consistency` | Classical | Speaker characteristic consistency |
| `splicing` | Classical | Abrupt feature / noise-floor boundaries |
| `waveform` | Classical | Amplitude discontinuities |
| `spectral` | Classical | STFT / spectral discontinuities |
| `compression` | Classical | Codec metadata observations |
| `noise_consistency` | Classical | Background noise changes |
| `silence` | Classical | Unnatural silence patterns |
| `metadata` | Classical | Container metadata inconsistencies |

## Classical Analysis

Classical detectors use numpy-only feature extraction (RMS, ZCR, STFT, MFCC summaries). Results are deterministic for the same input hash when no AI models are loaded.

Findings use neutral forensic language. Discontinuities are reported as observations, not fraud conclusions.

## AI Model Integration

Configure via environment variables:

```bash
AUDIO_SYNTHETIC_MODEL_ENABLED=true
AUDIO_SYNTHETIC_MODEL_PATH=/path/to/model
AUDIO_SYNTHETIC_MODEL_SHA256=<sha256>

AUDIO_VOICE_CLONE_MODEL_ENABLED=true
AUDIO_VOICE_CLONE_MODEL_PATH=/path/to/model
AUDIO_VOICE_CLONE_MODEL_SHA256=<sha256>

AUDIO_DEEPFAKE_MODEL_ENABLED=true
AUDIO_DEEPFAKE_MODEL_PATH=/path/to/model
AUDIO_DEEPFAKE_MODEL_SHA256=<sha256>
```

When disabled or missing:

- `status = unavailable`
- `confidence = null`
- No fabricated predictions

Loaded models are SHA-256 verified before use.

## Confidence Policy

| Source | Confidence |
|--------|------------|
| Unavailable AI model | `null` |
| Classical indicator | Algorithmic score when justified |
| Reference comparison | Similarity score (not identity proof) |

## Temporal Localization

Findings may include:

- `start_time_ms`, `end_time_ms`, `duration_ms`
- Supporting metrics in metadata
- Timeline and segment endpoints for navigation

Example: *"Acoustic characteristics differ from the surrounding segment (4.2–5.1 s)."*

## Reference Voice Comparison

Optional `reference_evidence_id` on `POST /api/v1/evidence/{id}/audio-analysis` loads reference audio and compares MFCC-derived features. This does **not** prove speaker identity.

## Artifacts

Derived artifacts (hashed, separate from original):

- `AI_AUDIO_FEATURES` — feature summary JSON
- `AI_AUDIO_WAVEFORM` — downsampled envelope JSON
- `AI_AUDIO_SPECTROGRAM` — band summary JSON
- `AI_AUDIO_TIMELINE` — timeline + segments JSON
- `AI_AUDIO_PREDICTION` — detector prediction manifest (when models run)

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/evidence/{evidence_id}/audio-analysis` | Queue analysis |
| GET | `/api/v1/evidence/{evidence_id}/audio-analysis` | List runs |
| GET | `/api/v1/audio-analysis/{analysis_id}` | Run detail |
| GET | `/api/v1/evidence/{evidence_id}/audio-findings` | List findings |
| GET | `/api/v1/audio-analysis/{analysis_id}/timeline` | Timeline entries |
| GET | `/api/v1/audio-analysis/{analysis_id}/segments` | Localized segments |
| GET | `/api/v1/audio-analysis/{analysis_id}/features` | Feature summary |

## Database

Migration `20260831_0010_add_audio_ai.py` creates:

- `audio_analysis_runs`
- `audio_ai_findings`
- `audio_ai_finding_regions`

## Security

- Bounded file size, duration, and decoded samples
- Safe subprocess invocation for ffmpeg (no shell, fixed arguments)
- Path traversal and decompression bomb protections via existing storage/validation layers
- Untrusted metadata never treated as proof of manipulation

## Limitations

- No final fraud/genuine scoring (Phase 6F / Jury / Fusion)
- AI detectors require externally supplied model weights
- Non-WAV decode requires ffmpeg
- Speaker identity is not validated without a configured identity model
- Pitch/formant analysis is simplified (numpy STFT-based)

## Frontend

`AudioAnalysisPanel` displays analysis status, audio metadata, detector badges, timeline, segments, findings, and unavailable AI model states with neutral language.
