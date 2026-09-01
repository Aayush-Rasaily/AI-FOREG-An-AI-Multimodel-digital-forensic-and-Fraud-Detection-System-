"""Standard-library WAV and optional ffprobe audio inspection."""

import asyncio
import json
import wave
from typing import Any

from backend.app.application.processors.base import DerivedArtifactPayload
from backend.app.domain.processing import ArtifactType
from backend.app.extraction.exceptions import (
    ExtractionCapabilityUnavailableError,
    ExtractionError,
)
from backend.app.extraction.media import probe_stream
from backend.app.extraction.models import (
    ExtractionContext,
    ExtractionItem,
    ExtractionResult,
    ExtractionSourceType,
    ExtractionStatus,
    ExtractionType,
)


class AudioExtractor:
    """Extract truthful WAV metadata and report unavailable codecs explicitly."""

    extensions = frozenset({"wav", "mp3", "m4a", "aac", "flac"})

    def can_extract(self, context: ExtractionContext) -> bool:
        """Support configured audio extensions and audio MIME values."""

        extension = context.original_filename.rsplit(".", 1)[-1].lower()
        return extension in self.extensions or context.mime_type.startswith("audio/")

    async def extract(self, context: ExtractionContext) -> ExtractionResult:
        """Inspect WAV using stdlib or other formats through optional ffprobe."""

        extension = context.original_filename.rsplit(".", 1)[-1].lower()
        metadata: dict[str, object] | None
        try:
            async with context.storage.open(context.storage_key) as stream:
                if extension == "wav":
                    metadata = await asyncio.to_thread(_read_wave, stream)
                else:
                    probe = await asyncio.to_thread(
                        probe_stream,
                        stream,
                        command=context.settings.ffprobe_command,
                    )
                    metadata = _audio_metadata_from_probe(probe)
        except ExtractionCapabilityUnavailableError as exc:
            return ExtractionResult(
                status=ExtractionStatus.UNAVAILABLE,
                metadata={"audio_metadata_status": "UNAVAILABLE"},
                error_code=exc.code,
                error_message_safe=exc.message,
            )
        except ExtractionError:
            raise
        except (OSError, EOFError, wave.Error) as exc:
            raise ExtractionError(
                "AUDIO_EXTRACTION_FAILED",
                "The audio file could not be safely inspected.",
            ) from exc

        if metadata is None:
            return ExtractionResult(
                status=ExtractionStatus.UNAVAILABLE,
                metadata={"audio_metadata_status": "UNAVAILABLE"},
                error_code="AUDIO_STREAM_UNAVAILABLE",
                error_message_safe="No audio stream was available for extraction.",
            )
        item = ExtractionItem(
            evidence_id=context.evidence_id,
            source_type=ExtractionSourceType.ORIGINAL,
            source_identifier=context.original_filename,
            extraction_type=ExtractionType.AUDIO_STREAM,
            content=json.dumps(metadata, sort_keys=True),
            method="wave_audio_metadata"
            if extension == "wav"
            else "ffprobe_audio_metadata",
            version="1.0",
            metadata=metadata,
        )
        return ExtractionResult(
            status=ExtractionStatus.SUCCEEDED,
            items=(item,),
            artifacts=(
                DerivedArtifactPayload(
                    artifact_type=ArtifactType.AUDIO_STREAM_INFO,
                    mime_type="application/json",
                    content=json.dumps(metadata, sort_keys=True).encode("utf-8"),
                    metadata={"stream_type": "audio"},
                ),
            ),
            metadata=metadata,
        )


def _read_wave(stream: Any) -> dict[str, object]:
    with wave.open(stream, "rb") as audio:
        sample_rate = audio.getframerate()
        frames = audio.getnframes()
        return {
            "duration": frames / sample_rate if sample_rate else None,
            "sample_rate": sample_rate,
            "channels": audio.getnchannels(),
            "sample_width_bytes": audio.getsampwidth(),
            "frame_count": frames,
            "codec": "PCM",
            "format": "WAV",
        }


def _audio_metadata_from_probe(probe: dict[str, Any]) -> dict[str, object] | None:
    streams = probe.get("streams", [])
    audio_stream = next(
        (
            stream
            for stream in streams
            if isinstance(stream, dict) and stream.get("codec_type") == "audio"
        ),
        None,
    )
    if not isinstance(audio_stream, dict):
        return None
    return {
        "duration": _number(audio_stream.get("duration"))
        or _number(probe.get("format", {}).get("duration")),
        "sample_rate": _integer(audio_stream.get("sample_rate")),
        "channels": _integer(audio_stream.get("channels")),
        "codec": audio_stream.get("codec_name"),
        "format": probe.get("format", {}).get("format_name"),
    }


def _number(value: object) -> float | None:
    try:
        return float(str(value)) if value is not None else None
    except (TypeError, ValueError):
        return None


def _integer(value: object) -> int | None:
    try:
        return int(str(value)) if value is not None else None
    except (TypeError, ValueError):
        return None
