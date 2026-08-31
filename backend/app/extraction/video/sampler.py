"""Deterministic, bounded video sampling schedule."""

from collections.abc import Iterable


def sample_timestamps(
    duration_seconds: float | None,
    interval_seconds: float,
    max_frames: int,
) -> tuple[int, ...]:
    """Return bounded timestamp requests without decoding or inventing frames."""

    if (
        duration_seconds is None
        or duration_seconds <= 0
        or interval_seconds <= 0
        or max_frames <= 0
    ):
        return ()
    timestamps: list[int] = []
    current = 0.0
    while current < duration_seconds and len(timestamps) < max_frames:
        timestamps.append(round(current * 1000))
        current += interval_seconds
    return tuple(timestamps)


def bounded_frame_numbers(
    timestamps_ms: Iterable[int],
    *,
    start: int = 0,
) -> tuple[tuple[int, int], ...]:
    """Pair requested timestamps with stable one-based frame numbers."""

    return tuple(
        (start + index + 1, timestamp)
        for index, timestamp in enumerate(timestamps_ms)
    )
