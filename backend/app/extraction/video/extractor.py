"""Bounded video metadata and frame-sampling capability adapter."""

import asyncio
import json

from backend.app.application.processors.base import DerivedArtifactPayload
from backend.app.domain.processing import ArtifactType
from backend.app.extraction.exceptions import ExtractionCapabilityUnavailableError
from backend.app.extraction.media import probe_stream
from backend.app.extraction.models import (
    ExtractionContext,
    ExtractionItem,
    ExtractionResult,
    ExtractionSourceType,
    ExtractionStatus,
    ExtractionType,
)
from backend.app.extraction.video.sampler import (
    bounded_frame_numbers,
    sample_timestamps,
)


class VideoExtractor:
    """Use optional ffprobe metadata without inventing frames."""

    extensions = frozenset({"mp4", "mov", "avi", "mkv", "webm"})

    def can_extract(self, context: ExtractionContext) -> bool:
        """Support configured video extensions and video MIME values."""

        extension = context.original_filename.rsplit(".", 1)[-1].lower()
        return extension in self.extensions or context.mime_type.startswith("video/")

    async def extract(self, context: ExtractionContext) -> ExtractionResult:
        """Inspect video streams when ffprobe is explicitly available."""

        try:
            async with context.storage.open(context.storage_key) as stream:
                probe = await asyncio.to_thread(
                    probe_stream,
                    stream,
                    command=context.settings.ffprobe_command,
                )
        except ExtractionCapabilityUnavailableError as exc:
            return ExtractionResult(
                status=ExtractionStatus.UNAVAILABLE,
                metadata={
                    "video_metadata_status": "UNAVAILABLE",
                    "frame_sampling_status": "UNAVAILABLE",
                },
                error_code=exc.code,
                error_message_safe=exc.message,
            )

        streams = probe.get("streams", [])
        video_stream = next(
            (
                stream
                for stream in streams
                if isinstance(stream, dict) and stream.get("codec_type") == "video"
            ),
            None,
        )
        if not isinstance(video_stream, dict):
            return ExtractionResult(
                status=ExtractionStatus.UNAVAILABLE,
                metadata={"video_metadata_status": "UNAVAILABLE"},
                error_code="VIDEO_STREAM_UNAVAILABLE",
                error_message_safe="No video stream was available for extraction.",
            )
        duration = _number(video_stream.get("duration")) or _number(
            probe.get("format", {}).get("duration")
        )
        metadata = {
            "duration": duration,
            "width": _integer(video_stream.get("width")),
            "height": _integer(video_stream.get("height")),
            "fps": _frame_rate(video_stream.get("avg_frame_rate")),
            "frame_count": _integer(video_stream.get("nb_frames")),
            "codec": video_stream.get("codec_name"),
            "container": probe.get("format", {}).get("format_name"),
            "sample_interval_seconds": context.settings.media_sample_interval_seconds,
            "max_frames": context.settings.media_max_frames,
            "frame_sampling_status": "UNAVAILABLE",
            "frame_sampling_error_code": "FFMPEG_UNAVAILABLE",
        }
        requested_frames = bounded_frame_numbers(
            sample_timestamps(
                duration,
                context.settings.media_sample_interval_seconds,
                context.settings.media_max_frames,
            )
        )
        metadata["requested_frame_timestamps"] = [
            {
                "frame_number": frame_number,
                "timestamp_ms": timestamp_ms,
            }
            for frame_number, timestamp_ms in requested_frames
        ]
        item = ExtractionItem(
            evidence_id=context.evidence_id,
            source_type=ExtractionSourceType.ORIGINAL,
            source_identifier=context.original_filename,
            extraction_type=ExtractionType.METADATA,
            content=json.dumps(metadata, sort_keys=True),
            method="ffprobe_video_metadata",
            version="1.0",
            metadata=metadata,
        )
        frame_index = {
            "frames": [],
            "requested_frames": metadata["requested_frame_timestamps"],
            "sample_interval_seconds": context.settings.media_sample_interval_seconds,
            "max_frames": context.settings.media_max_frames,
            "status": "UNAVAILABLE",
            "error_code": "FFMPEG_UNAVAILABLE",
        }
        return ExtractionResult(
            status=ExtractionStatus.PARTIAL,
            items=(item,),
            artifacts=(
                DerivedArtifactPayload(
                    artifact_type=ArtifactType.VIDEO_FRAME_INDEX,
                    mime_type="application/json",
                    content=json.dumps(frame_index, sort_keys=True).encode("utf-8"),
                    metadata={"frames_sampled": 0},
                ),
            ),
            metadata=metadata,
            error_code="FFMPEG_UNAVAILABLE",
            error_message_safe=(
                "Video metadata was extracted; frame sampling is unavailable."
            ),
        )


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


def _frame_rate(value: object) -> float | None:
    if not isinstance(value, str) or "/" not in value:
        return _number(value)
    numerator, denominator = value.split("/", 1)
    try:
        return float(numerator) / float(denominator)
    except (ValueError, ZeroDivisionError):
        return None
