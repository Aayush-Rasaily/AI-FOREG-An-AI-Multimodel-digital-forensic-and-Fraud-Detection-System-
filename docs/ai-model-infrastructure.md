# AI Model Infrastructure

Phase 6A provides a production-grade inference framework for AI-FORGE. It does **not** perform forensic AI detection. It establishes the registry, device management, caching, preprocessing, postprocessing, and persistence layers that every future model will use.

## Architecture

```text
API (FastAPI)
    ↓
AIService
    ↓
ModelRegistry → ModelLoader → CacheManager
    ↓
AIInferenceEngine
    ├── Preprocessors (image/document/video/audio)
    ├── DeviceManager
    ├── AIModel.predict()
    └── Postprocessing → NormalizedInferenceOutput
    ↓
AIRepository → AIModelRecord / InferenceJob / InferenceLog
```

## Model Registry

`ModelRegistry` (`backend/app/ai/registry/registry.py`) manages pluggable models without switch-based dispatch.

- **register(factory)** — each model registers via factory callable
- **unregister(name)** — remove and unload
- **reload(name)** — fresh instance for hot-swapping
- **lookup(name)** — get or create active instance
- **list_metadata()** — capability discovery
- **discover_capabilities()** — task map by model

Built-in registration happens in `build_registry()` (`backend/app/ai/bootstrap.py`), which registers `DummyModel` for infrastructure verification.

## Model Lifecycle

1. Model factory registers with `ModelRegistry` at application startup.
2. Metadata sync persists `AIModelRecord` rows via `AIService.sync_registry()`.
3. `POST /api/v1/models/reload` evicts cache, reloads weights interface, warms up, runs infrastructure inference, and logs an `InferenceJob`.
4. `AIInferenceEngine.run()` validates requests, preprocesses inputs, selects device, executes `predict()`, normalizes output, and returns `InferenceResponse`.
5. `CacheManager` retains loaded instances until eviction or TTL expiry.

## AIModel Contract

Every model implements:

- `load(device)` / `unload()` / `warmup(batch_size)`
- `async predict(inputs, batch_size)`
- `metadata()` → `ModelMetadata`
- `supports(task)` / `health()` / `version()`

`DummyModel` returns deterministic infrastructure output only (`infrastructure_check: passed`). It never emits forensic predictions.

## Provider Abstraction

Framework providers initialize runtime detection only — they do not perform inference:

| Provider | Module |
|----------|--------|
| PyTorch | `providers/pytorch_provider.py` |
| ONNX | `providers/onnx_provider.py` |
| TensorFlow | `providers/tensorflow_provider.py` |

Future models will select a provider based on `ModelMetadata.framework`.

## Cache

`CacheManager` (`backend/app/ai/cache/manager.py`):

- LRU-ordered in-memory cache with configurable `max_models` and TTL
- Tracks hits, misses, evictions
- Exposes per-model cache state for the AI Models page

## Device Selection

`DeviceManager` (`backend/app/ai/device/manager.py`):

- Detects CPU and CUDA (when PyTorch is installed)
- Placeholder flags for Apple MPS, ROCm, TensorRT
- `select_device(required)` chooses the best available backend

## Preprocessing

Reusable modality preprocessors live under `backend/app/ai/preprocessing/`:

- **image** — resize, normalize, pad, tile
- **document** — page/region interfaces
- **video** — frame sampling interface
- **audio** — resampling interface

Preprocessors are registered in a dict on `AIInferenceEngine` — no switch statements.

## Postprocessing

All model outputs pass through `normalize_raw_output()` into `NormalizedInferenceOutput`. Arbitrary dict responses from models are converted into structured `NormalizedOutputItem` entries.

## Database

| Table | Purpose |
|-------|---------|
| `ai_model_records` | Registered model metadata and runtime state |
| `inference_jobs` | Tracked inference/reload executions |
| `inference_logs` | Structured job log entries |

Migration: `20260831_0006_add_ai_infrastructure.py`

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/models` | List models, devices, cache stats |
| GET | `/api/v1/models/{id}` | One model detail |
| POST | `/api/v1/models/reload` | Reload and warmup |
| GET | `/api/v1/inference/jobs` | Job history |
| GET | `/api/v1/inference/jobs/{id}` | One job with logs |

## Dependency Injection

The AI stack is composed once in `create_app()` and stored on `app.state.ai_stack`. `get_ai_service()` builds a request-scoped `AIService` with the shared registry, cache, and engine.

## Future Extension Guide

1. Subclass `AIModel` with your model implementation.
2. Register the factory in `build_registry()`.
3. Add preprocessor entry if a new modality is required.
4. Optionally extend a `BasePipeline` subclass for end-to-end modality flows.
5. Wire real artifact loading through `ModelLoader.load_model()` with `ModelFormat`.
6. Run `POST /models/reload` to hot-swap after deployment.

Do **not** add forensic verdict logic to the infrastructure layer. Forensic models belong in later phases and must return normalized outputs through the same postprocessing envelope.
