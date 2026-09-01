"""Bounded video frame sampling and extraction."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from backend.app.ai.video.models.base import VideoFrameReference
from backend.app.extraction.video.sampler import (
    bounded_frame_numbers,
    sample_timestamps,
)


def frame_identifier(source_sha256: str, frame_index: int, timestamp_ms: int) -> str:
    """Return a deterministic frame identifier."""

    payload = f"{source_sha256}:{frame_index}:{timestamp_ms}".encode()
    return hashlib.sha256(payload).hexdigest()


def build_frame_schedule(
    *,
    duration_seconds: float | None,
    interval_seconds: float,
    max_frames: int,
    source_sha256: str,
) -> tuple[VideoFrameReference, ...]:
    """Build bounded deterministic frame references from sampling config."""

    timestamps = sample_timestamps(duration_seconds, interval_seconds, max_frames)
    pairs = bounded_frame_numbers(timestamps)
    frames: list[VideoFrameReference] = []
    for index, (frame_number, timestamp_ms) in enumerate(pairs):
        frames.append(
            VideoFrameReference(
                frame_index=index,
                frame_number=frame_number,
                timestamp_ms=timestamp_ms,
                timestamp_seconds=round(timestamp_ms / 1000.0, 3),
                source_video_hash=source_sha256,
                frame_id=frame_identifier(source_sha256, index, timestamp_ms),
            )
        )
    return tuple(frames)


def parse_frame_index(raw: bytes | None) -> dict[str, Any]:
    """Parse a VIDEO_FRAME_INDEX artifact payload."""

    if not raw:
        return {}
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def schedule_from_frame_index(
    frame_index: dict[str, Any],
    *,
    source_sha256: str,
    interval_seconds: float,
    max_frames: int,
    duration_seconds: float | None,
) -> tuple[VideoFrameReference, ...]:
    """Build frame schedule from extraction artifact or fallback sampling."""

    requested = frame_index.get("requested_frames")
    if isinstance(requested, list) and requested:
        frames: list[VideoFrameReference] = []
        for index, entry in enumerate(requested[:max_frames]):
            if not isinstance(entry, dict):
                continue
            frame_number = int(entry.get("frame_number", index + 1))
            timestamp_ms = int(entry.get("timestamp_ms", 0))
            frames.append(
                VideoFrameReference(
                    frame_index=index,
                    frame_number=frame_number,
                    timestamp_ms=timestamp_ms,
                    timestamp_seconds=round(timestamp_ms / 1000.0, 3),
                    source_video_hash=source_sha256,
                    frame_id=frame_identifier(source_sha256, index, timestamp_ms),
                )
            )
        if frames:
            return tuple(frames)
    return build_frame_schedule(
        duration_seconds=duration_seconds,
        interval_seconds=interval_seconds,
        max_frames=max_frames,
        source_sha256=source_sha256,
    )


def ffmpeg_available(command: str = "ffmpeg") -> bool:
    """Return whether ffmpeg is available on the host."""

    return shutil.which(command) is not None


def extract_frame_at_timestamp(
    video_path: Path,
    *,
    timestamp_seconds: float,
    ffmpeg_command: str = "ffmpeg",
) -> tuple[np.ndarray, int, int] | None:
    """Extract one frame using ffmpeg without loading the full video."""

    executable = shutil.which(ffmpeg_command)
    if not executable:
        return None
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temporary:
        output_path = Path(temporary.name)
    try:
        result = subprocess.run(
            [
                executable,
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                f"{timestamp_seconds:.3f}",
                "-i",
                str(video_path),
                "-frames:v",
                "1",
                "-f",
                "image2pipe",
                "-vcodec",
                "png",
                str(output_path),
            ],
            capture_output=True,
            check=False,
            timeout=30,
        )
        if result.returncode != 0 or not output_path.exists():
            return None
        with Image.open(output_path) as image:
            rgb = np.asarray(image.convert("RGB"))
        height, width = rgb.shape[:2]
        return rgb, width, height
    except (subprocess.TimeoutExpired, OSError, ValueError):
        return None
    finally:
        output_path.unlink(missing_ok=True)


def decode_sampled_frames(
    stream: Any,
    schedule: tuple[VideoFrameReference, ...],
    *,
    ffmpeg_command: str = "ffmpeg",
    max_frames: int = 120,
) -> tuple[VideoFrameReference, ...]:
    """Decode bounded frames when ffmpeg is available."""

    if not schedule or not ffmpeg_available(ffmpeg_command):
        return schedule
    bounded = schedule[:max_frames]
    with tempfile.NamedTemporaryFile(suffix=".video", delete=False) as temporary:
        video_path = Path(temporary.name)
        shutil.copyfileobj(stream, temporary, length=1024 * 1024)
    decoded: list[VideoFrameReference] = []
    try:
        for frame in bounded:
            extracted = extract_frame_at_timestamp(
                video_path,
                timestamp_seconds=frame.timestamp_seconds,
                ffmpeg_command=ffmpeg_command,
            )
            if extracted is None:
                decoded.append(frame)
                continue
            rgb, width, height = extracted
            decoded.append(
                VideoFrameReference(
                    frame_index=frame.frame_index,
                    frame_number=frame.frame_number,
                    timestamp_ms=frame.timestamp_ms,
                    timestamp_seconds=frame.timestamp_seconds,
                    source_video_hash=frame.source_video_hash,
                    frame_id=frame.frame_id,
                    width=width,
                    height=height,
                    image_array=rgb,
                )
            )
    finally:
        video_path.unlink(missing_ok=True)
    return tuple(decoded)


def encode_frame_png(frame: np.ndarray) -> bytes:
    """Encode an RGB frame as PNG bytes."""

    buffer = BytesIO()
    Image.fromarray(frame.astype(np.uint8), mode="RGB").save(buffer, format="PNG")
    return buffer.getvalue()
