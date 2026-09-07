"""Malware-safe upload validation helpers (Phase 10D)."""

from __future__ import annotations

import hashlib
import io
import zipfile
from pathlib import PurePath

from backend.app.core.exceptions import InvalidFileError, UnsupportedFileError
from backend.app.security.validation import reject_path_traversal

DANGEROUS_EXTENSIONS: frozenset[str] = frozenset(
    {
        "exe",
        "bat",
        "cmd",
        "com",
        "scr",
        "ps1",
        "vbs",
        "js",
        "jar",
        "msi",
        "dll",
        "sh",
        "bash",
        "php",
        "phtml",
        "asp",
        "aspx",
        "cgi",
        "hta",
        "lnk",
    }
)


def normalize_upload_filename(filename: str | None) -> str:
    """Return a basename-only filename after rejecting unsafe patterns."""

    if not filename or not filename.strip():
        raise InvalidFileError("The uploaded filename is empty.")
    raw = filename.strip()
    if "\x00" in raw:
        raise InvalidFileError("The uploaded filename contains a null byte.")
    if any(ord(ch) < 32 for ch in raw):
        raise InvalidFileError("The uploaded filename contains control characters.")
    if len(raw) > 255:
        raise InvalidFileError("The uploaded filename is too long.")
    try:
        reject_path_traversal(raw)
    except ValueError as exc:
        raise InvalidFileError(str(exc)) from exc
    if "/" in raw or "\\" in raw:
        raise InvalidFileError("The uploaded filename is unsafe.")
    name = PurePath(raw).name
    if name != raw or name in {".", ".."} or not name:
        raise InvalidFileError("The uploaded filename is unsafe.")
    # Double-extension tricks such as invoice.pdf.exe
    parts = name.lower().split(".")
    if len(parts) >= 3:
        for part in parts[1:-1]:
            if part in DANGEROUS_EXTENSIONS:
                raise UnsupportedFileError("The uploaded filename is unsafe.")
    extension = parts[-1] if len(parts) > 1 else ""
    if extension in DANGEROUS_EXTENSIONS:
        raise UnsupportedFileError("The uploaded file extension is not allowed.")
    return name


def assert_upload_size(file_size: int, *, max_bytes: int) -> None:
    if file_size <= 0:
        raise InvalidFileError("The uploaded file is empty.")
    if file_size > max_bytes:
        from backend.app.core.exceptions import FileTooLargeError

        raise FileTooLargeError("The uploaded file exceeds the size limit.")


def content_fingerprint(data: bytes) -> str:
    """Stable SHA-256 fingerprint for duplicate detection."""

    return hashlib.sha256(data).hexdigest()


def scan_archive_for_traversal(
    data: bytes,
    *,
    ignore_truncated: bool = False,
) -> None:
    """Reject ZIP-based uploads with path traversal or absolute member paths."""

    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            for info in archive.infolist():
                name = info.filename
                if not name:
                    continue
                normalized = name.replace("\\", "/")
                if (
                    normalized.startswith("/")
                    or normalized.startswith("../")
                    or "/../" in normalized
                    or normalized.endswith("/..")
                    or normalized == ".."
                ):
                    raise InvalidFileError(
                        "The uploaded archive contains an unsafe path."
                    )
                if info.file_size < 0 or info.compress_size < 0:
                    raise InvalidFileError("The uploaded archive is malformed.")
    except zipfile.BadZipFile as exc:
        if ignore_truncated:
            return
        raise InvalidFileError("The uploaded archive is malformed.") from exc


def harden_upload_metadata(filename: str | None, content_type: str | None) -> str:
    """Shared pre-check used before category/MIME policy validation."""

    safe_name = normalize_upload_filename(filename)
    if content_type is not None and "\x00" in content_type:
        raise InvalidFileError("The uploaded content type is unsafe.")
    return safe_name
