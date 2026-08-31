"""Optional, safely-invoked ffprobe adapter for media metadata."""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, BinaryIO

from backend.app.extraction.exceptions import (
    ExtractionCapabilityUnavailableError,
    ExtractionError,
)


def probe_stream(
    stream: BinaryIO,
    *,
    command: str,
) -> dict[str, Any]:
    """Copy a read-only stream to a temporary file and run fixed ffprobe args."""

    executable = shutil.which(command)
    if not executable:
        raise ExtractionCapabilityUnavailableError(
            "MEDIA_PARSER_UNAVAILABLE",
            "The configured media parser executable is unavailable.",
        )
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix="ai-forge-media-",
            suffix=".input",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            shutil.copyfileobj(stream, temporary, length=1024 * 1024)
        result = subprocess.run(
            [
                executable,
                "-v",
                "error",
                "-print_format",
                "json",
                "-show_streams",
                "-show_format",
                str(temporary_path),
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        if result.returncode != 0:
            raise ExtractionError(
                "MEDIA_EXTRACTION_FAILED",
                "The media file could not be safely inspected.",
            )
        try:
            parsed = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise ExtractionError(
                "MEDIA_METADATA_INVALID",
                "The media parser returned invalid metadata.",
            ) from exc
        if not isinstance(parsed, dict):
            raise ExtractionError(
                "MEDIA_METADATA_INVALID",
                "The media parser returned invalid metadata.",
            )
        return parsed
    except subprocess.TimeoutExpired as exc:
        raise ExtractionError(
            "MEDIA_EXTRACTION_TIMEOUT",
            "The media parser exceeded its time limit.",
        ) from exc
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
