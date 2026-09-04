"""Deterministic ZIP archive builder."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

from backend.app.interoperability.hashing import sha256_bytes
from backend.app.interoperability.policy import DETERMINISTIC_ZIP_DATE


def build_deterministic_zip(files: dict[str, bytes]) -> bytes:
    """Build a ZIP with stable member order and fixed timestamps.

    ``files`` maps archive-relative paths to payloads. Paths are sorted.
    ZipInfo dates use ``DETERMINISTIC_ZIP_DATE`` so identical payloads yield
    identical archive bytes (documented exception: none in the ZIP binary).
    """

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in sorted(files.keys()):
            info = zipfile.ZipInfo(filename=name, date_time=DETERMINISTIC_ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 0
            zf.writestr(info, files[name])
    return buffer.getvalue()


def write_deterministic_zip(path: Path, files: dict[str, bytes]) -> str:
    """Write a deterministic ZIP to disk and return its SHA-256."""

    payload = build_deterministic_zip(files)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return sha256_bytes(payload)


def read_zip_members(path: Path) -> dict[str, bytes]:
    """Read all ZIP members into a path→bytes map."""

    result: dict[str, bytes] = {}
    with zipfile.ZipFile(path, mode="r") as zf:
        for name in sorted(zf.namelist()):
            if name.endswith("/"):
                continue
            result[name] = zf.read(name)
    return result
