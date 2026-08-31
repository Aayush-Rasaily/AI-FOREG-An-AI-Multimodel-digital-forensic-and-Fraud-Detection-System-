"""Deterministic tests for streaming storage, hashing, and cleanup safety."""

from io import BytesIO
from pathlib import Path

import pytest

from backend.app.application.services.file_validation import FileValidationService
from backend.app.application.services.hashing import HashService
from backend.app.core.config import Settings
from backend.app.core.exceptions import (
    FileTooLargeError,
    InvalidFileError,
    StorageError,
    UnsupportedFileError,
)
from backend.app.infrastructure.storage.local import LocalStorage


@pytest.mark.asyncio
async def test_local_storage_and_hash_service_preserve_streamed_bytes(
    tmp_path: Path,
) -> None:
    """Staged bytes can be hashed deterministically and committed exclusively."""

    storage = LocalStorage(tmp_path / "data")
    temporary_key = storage.temporary_key()
    content = b"%PDF-1.7\n" + b"evidence" * 10_000
    size = await storage.save_stream(
        BytesIO(content),
        temporary_key,
        max_bytes=len(content) + 1,
        chunk_size=4096,
    )
    assert size == len(content)

    async with storage.open(temporary_key) as stream:
        hash_service = HashService()
        first = await hash_service.hash_stream(stream, chunk_size=4096)
    async with storage.open(temporary_key) as stream:
        second = await hash_service.hash_stream(stream, chunk_size=4096)
    assert first == second
    assert first.file_size == len(content)

    final_key = "evidence/case/evidence/original/generated.pdf"
    await storage.commit(temporary_key, final_key)
    assert await storage.exists(final_key)
    assert not await storage.exists(temporary_key)
    with pytest.raises(StorageError):
        await storage.commit("missing", final_key)


@pytest.mark.asyncio
async def test_local_storage_rejects_oversized_stream_and_cleans_partial_object(
    tmp_path: Path,
) -> None:
    """Size failures remove partial objects from the staging area."""

    storage = LocalStorage(tmp_path / "data")
    temporary_key = storage.temporary_key()
    with pytest.raises(FileTooLargeError):
        await storage.save_stream(
            BytesIO(b"123456789"),
            temporary_key,
            max_bytes=4,
            chunk_size=4,
        )
    assert not await storage.exists(temporary_key)


def test_file_validation_rejects_unsafe_and_mismatched_metadata(
    tmp_path: Path,
) -> None:
    """Filename traversal and unsupported MIME combinations are blocked."""

    settings = Settings(storage_root=tmp_path / "data")
    validator = FileValidationService(settings)
    with pytest.raises(InvalidFileError):
        validator.validate_metadata("../evidence.pdf", "application/pdf")
    with pytest.raises(UnsupportedFileError):
        validator.validate_metadata("evidence.exe", "application/octet-stream")


@pytest.mark.asyncio
async def test_file_validation_checks_content_signature(tmp_path: Path) -> None:
    """A declared PDF with non-PDF bytes is not accepted."""

    validator = FileValidationService(Settings(storage_root=tmp_path / "data"))
    descriptor = validator.validate_metadata("evidence.pdf", "application/pdf")
    with pytest.raises(InvalidFileError):
        await validator.validate_content(BytesIO(b"not a pdf"), descriptor)
