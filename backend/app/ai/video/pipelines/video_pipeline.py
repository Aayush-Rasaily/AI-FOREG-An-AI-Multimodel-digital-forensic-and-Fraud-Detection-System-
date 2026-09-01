"""Video analysis pipeline orchestration."""

from __future__ import annotations

import json

from backend.app.ai.video.models.base import VideoFrameReference
from backend.app.ai.video.models.context import VideoAnalysisContext
from backend.app.ai.video.preprocessing.frames import (
    decode_sampled_frames,
    encode_frame_png,
    ffmpeg_available,
    schedule_from_frame_index,
)
from backend.app.application.processors.base import DerivedArtifactPayload
from backend.app.domain.processing import ArtifactType


async def prepare_video_context(
    context: VideoAnalysisContext,
) -> tuple[VideoAnalysisContext, tuple[DerivedArtifactPayload, ...]]:
    """Build sampled frames and derived artifacts for analysis."""

    duration_seconds = (
        context.duration_ms / 1000.0 if context.duration_ms is not None else None
    )
    schedule = schedule_from_frame_index(
        context.frame_index_artifact,
        source_sha256=context.source_sha256,
        interval_seconds=context.video_settings.sample_interval_seconds,
        max_frames=context.video_settings.max_frames,
        duration_seconds=duration_seconds,
    )
    artifacts: list[DerivedArtifactPayload] = []
    decoded_frames: tuple[VideoFrameReference, ...] = schedule
    if ffmpeg_available(context.video_settings.ffmpeg_command):
        async with context.storage.open(context.storage_key) as stream:
            decoded_frames = decode_sampled_frames(
                stream,
                schedule,
                ffmpeg_command=context.video_settings.ffmpeg_command,
                max_frames=context.video_settings.max_frames,
            )
    for frame in decoded_frames:
        if frame.image_array is None:
            continue
        artifacts.append(
            DerivedArtifactPayload(
                artifact_type=ArtifactType.AI_VIDEO_FRAME,
                mime_type="image/png",
                content=encode_frame_png(frame.image_array),
                metadata={
                    "frame_number": frame.frame_number,
                    "timestamp_ms": frame.timestamp_ms,
                    "frame_id": frame.frame_id,
                },
            )
        )
    timeline_payload = {
        "frames": [frame.to_dict() for frame in decoded_frames],
        "frame_sampling_available": any(
            frame.image_array is not None for frame in decoded_frames
        ),
    }
    artifacts.append(
        DerivedArtifactPayload(
            artifact_type=ArtifactType.AI_VIDEO_TIMELINE,
            mime_type="application/json",
            content=json.dumps(timeline_payload, sort_keys=True).encode("utf-8"),
            metadata={"frames_sampled": len(decoded_frames)},
        )
    )
    updated = VideoAnalysisContext(
        evidence_id=context.evidence_id,
        case_id=context.case_id,
        original_filename=context.original_filename,
        mime_type=context.mime_type,
        storage_key=context.storage_key,
        classification=context.classification,
        source_sha256=context.source_sha256,
        storage=context.storage,
        settings=context.settings,
        video_settings=context.video_settings,
        duration_ms=context.duration_ms,
        fps=context.fps,
        frame_count=context.frame_count,
        width=context.width,
        height=context.height,
        codec=context.codec,
        container=context.container,
        sampled_frames=decoded_frames,
        frame_index_artifact=context.frame_index_artifact,
        extraction_metadata=context.extraction_metadata,
        extraction_artifacts=context.extraction_artifacts,
        device=context.device,
        preprocessing={
            **context.preprocessing,
            "frames_sampled": len(decoded_frames),
            "ffmpeg_available": ffmpeg_available(context.video_settings.ffmpeg_command),
        },
    )
    return updated, tuple(artifacts)
