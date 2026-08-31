"""Read-only evidence integrity inspection processor."""

import logging
from pathlib import PurePath

from backend.app.application.processors.base import (
    InspectionResult,
    ProcessorContext,
    ProcessorResult,
)
from backend.app.application.services.hashing import HashService
from backend.app.application.services.storage import StorageService
from backend.app.core.exceptions import ProcessingError

logger = logging.getLogger(__name__)


class FileInspectionProcessor:
    """Verify that the stored original still matches registered evidence."""

    def __init__(self, storage: StorageService, hash_service: HashService) -> None:
        self.storage = storage
        self.hash_service = hash_service

    def can_process(self, _context: ProcessorContext) -> bool:
        """Inspection is required for every processing pipeline."""

        return True

    async def process(self, context: ProcessorContext) -> ProcessorResult:
        """Hash the original in read-only mode and compare registered facts."""

        if not await self.storage.exists(context.evidence.storage_key):
            raise ProcessingError(
                "EVIDENCE_FILE_MISSING",
                "The registered evidence file is no longer available.",
            )

        async with self.storage.open(context.evidence.storage_key) as stream:
            result = await self.hash_service.hash_stream(
                stream,
                chunk_size=1024 * 1024,
            )

        extension = (
            PurePath(context.evidence.original_filename).suffix.lower().lstrip(".")
        )
        verified = (
            result.file_size == context.evidence.file_size
            and result.sha256_hash == context.evidence.sha256_hash
        )
        if not verified:
            logger.error(
                "Evidence integrity mismatch",
                extra={
                    "evidence_id": str(context.evidence.id),
                    "severity": "high",
                },
            )
            raise ProcessingError(
                "EVIDENCE_INTEGRITY_MISMATCH",
                "The stored evidence failed its integrity verification.",
            )

        inspection = InspectionResult(
            file_exists=True,
            file_size=result.file_size,
            extension=extension,
            mime_type=context.evidence.mime_type,
            sha256_hash=result.sha256_hash,
            sha256_verified=True,
        )
        return ProcessorResult(inspection=inspection)
