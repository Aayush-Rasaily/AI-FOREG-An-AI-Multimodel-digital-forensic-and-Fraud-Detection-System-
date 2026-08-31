"""Untrusted evidence filename, type, size, and signature validation."""

import asyncio
from dataclasses import dataclass
from pathlib import PurePath
from typing import BinaryIO

from backend.app.core.config import Settings
from backend.app.core.exceptions import (
    FileTooLargeError,
    InvalidFileError,
    UnsupportedFileError,
)


@dataclass(frozen=True, slots=True)
class ValidatedFile:
    """Normalized metadata accepted for evidence ingestion."""

    original_filename: str
    extension: str
    mime_type: str
    category: str


class FileValidationService:
    """Validate uploads against centrally configured type and size policy."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def validate_metadata(
        self,
        filename: str | None,
        content_type: str | None,
    ) -> ValidatedFile:
        """Validate filename, extension, and declared MIME category."""

        if not filename or not filename.strip():
            raise InvalidFileError("The uploaded filename is empty.")
        if "\x00" in filename or "/" in filename or "\\" in filename:
            raise InvalidFileError("The uploaded filename is unsafe.")
        if len(filename) > 255 or any(ord(character) < 32 for character in filename):
            raise InvalidFileError("The uploaded filename is unsafe.")
        if PurePath(filename).name != filename:
            raise InvalidFileError("The uploaded filename is unsafe.")

        extension = PurePath(filename).suffix.lower().lstrip(".")
        if not extension:
            raise UnsupportedFileError("The uploaded file has no supported extension.")

        category = next(
            (
                name
                for name, extensions in self.settings.supported_extensions.items()
                if extension in {value.lower().lstrip(".") for value in extensions}
            ),
            None,
        )
        if category is None:
            raise UnsupportedFileError("The uploaded file extension is not supported.")

        normalized_mime = (content_type or "").split(";", 1)[0].strip().lower()
        allowed_mimes = {
            value.lower()
            for value in self.settings.supported_mime_types.get(category, [])
        }
        if normalized_mime not in allowed_mimes:
            raise UnsupportedFileError("The uploaded MIME type is not supported.")

        return ValidatedFile(filename, extension, normalized_mime, category)

    async def validate_content(
        self,
        stream: BinaryIO,
        validated_file: ValidatedFile,
    ) -> None:
        """Reject obviously mismatched content using bounded magic-byte reads."""

        header = await asyncio.to_thread(stream.read, 64)
        if not header or not self._matches_signature(header, validated_file):
            raise InvalidFileError("The uploaded content does not match its file type.")

    def validate_size(self, file_size: int) -> None:
        """Enforce the configured maximum after streamed ingestion."""

        max_bytes = self.settings.max_upload_size_mb * 1024 * 1024
        if file_size <= 0:
            raise InvalidFileError("The uploaded file is empty.")
        if file_size > max_bytes:
            raise FileTooLargeError("The uploaded file exceeds the size limit.")

    @staticmethod
    def _matches_signature(header: bytes, file: ValidatedFile) -> bool:
        """Return whether a header is compatible with the supported category."""

        extension = file.extension
        if extension in {"jpg", "jpeg"}:
            return header.startswith(b"\xff\xd8\xff")
        if extension == "png":
            return header.startswith(b"\x89PNG\r\n\x1a\n")
        if extension == "webp":
            return header.startswith(b"RIFF") and header[8:12] == b"WEBP"
        if extension in {"tif", "tiff"}:
            return header.startswith((b"II*\x00", b"MM\x00*"))
        if extension == "pdf":
            return header.startswith(b"%PDF-")
        if extension == "docx":
            return header.startswith(b"PK")
        if extension in {"mp4", "m4a"}:
            return len(header) >= 12 and header[4:8] == b"ftyp"
        if extension == "mov":
            return len(header) >= 12 and header[4:8] == b"ftyp"
        if extension == "avi":
            return header.startswith(b"RIFF") and header[8:12] == b"AVI "
        if extension in {"mkv", "webm"}:
            return header.startswith(b"\x1aE\xdf\xa3")
        if extension == "wav":
            return header.startswith(b"RIFF") and header[8:12] == b"WAVE"
        if extension == "mp3":
            return header.startswith(b"ID3") or (
                len(header) >= 2 and header[0] == 0xFF and header[1] & 0xE0 == 0xE0
            )
        if extension == "aac":
            return len(header) >= 2 and header[0] == 0xFF and header[1] & 0xF6 == 0xF0
        if extension == "flac":
            return header.startswith(b"fLaC")
        return False
