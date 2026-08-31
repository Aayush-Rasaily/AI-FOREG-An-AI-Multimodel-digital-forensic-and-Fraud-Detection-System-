"""Application service for evidence ingestion and metadata retrieval."""

import asyncio
import logging
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.schemas.evidence import EvidenceListResponse, EvidenceResponse
from backend.app.application.services.custody_service import ChainOfCustodyService
from backend.app.application.services.file_validation import FileValidationService
from backend.app.application.services.hashing import HashService
from backend.app.application.services.storage import StorageService
from backend.app.core.config import Settings
from backend.app.core.exceptions import ConflictError, ResourceNotFoundError
from backend.app.domain.evidence import EvidenceStatus
from backend.app.infrastructure.database.repositories.case import CaseRepository
from backend.app.infrastructure.database.repositories.evidence import EvidenceRepository
from backend.app.models.evidence import Evidence

logger = logging.getLogger(__name__)


class EvidenceService:
    """Coordinate safe evidence ingestion without implementing analysis."""

    def __init__(
        self,
        session: AsyncSession,
        storage: StorageService,
        hash_service: HashService,
        validation_service: FileValidationService,
        settings: Settings,
    ) -> None:
        self.session = session
        self.settings = settings
        self.storage = storage
        self.hash_service = hash_service
        self.validation_service = validation_service
        self.case_repository = CaseRepository(session)
        self.repository = EvidenceRepository(session)
        self.custody_service = ChainOfCustodyService(session)

    async def ingest(
        self,
        case_id: UUID,
        upload: UploadFile,
    ) -> EvidenceResponse:
        """Validate, hash, persist, and record custody for one upload."""

        validated_file = self.validation_service.validate_metadata(
            upload.filename,
            upload.content_type,
        )
        case = await self.case_repository.get(case_id)
        if case is None:
            raise ResourceNotFoundError("The requested case was not found.")

        temporary_key = self.storage.temporary_key()
        final_key: str | None = None
        evidence_id: UUID | None = None
        registered = False
        logger.info("Evidence ingestion started", extra={"case_id": str(case_id)})

        try:
            await upload.seek(0)
            file_size = await self.storage.save_stream(
                upload.file,
                temporary_key,
                max_bytes=self.settings.max_upload_size_mb * 1024 * 1024,
                chunk_size=self.settings.upload_chunk_size_bytes,
            )
            self.validation_service.validate_size(file_size)

            async with self.storage.open(temporary_key) as staged_stream:
                await self.validation_service.validate_content(
                    staged_stream,
                    validated_file,
                )
                await asyncio.to_thread(staged_stream.seek, 0)
                hash_result = await self.hash_service.hash_stream(
                    staged_stream,
                    chunk_size=self.settings.upload_chunk_size_bytes,
                )

            duplicate = await self.repository.get_by_hash(
                case_id,
                hash_result.sha256_hash,
            )
            if duplicate is not None:
                raise ConflictError(
                    "The same evidence bytes are already registered for this case."
                )

            evidence_id = uuid4()
            evidence_number = await self.repository.next_evidence_number()
            stored_filename = f"{evidence_id.hex}.{validated_file.extension}"
            final_key = f"evidence/{case_id}/{evidence_id}/original/{stored_filename}"
            await self.storage.commit(temporary_key, final_key)

            evidence = Evidence(
                id=evidence_id,
                case_id=case_id,
                evidence_number=evidence_number,
                original_filename=validated_file.original_filename,
                stored_filename=stored_filename,
                mime_type=validated_file.mime_type,
                file_size=hash_result.file_size,
                sha256_hash=hash_result.sha256_hash,
                storage_key=final_key,
                status=EvidenceStatus.REGISTERED,
                metadata_json={},
            )

            await self.session.rollback()
            async with self.session.begin():
                await self.repository.add(evidence)
                custody_event = await self.custody_service.record_ingestion(
                    evidence_id=evidence.id,
                    sha256_hash=evidence.sha256_hash,
                )
            registered = True

            logger.info(
                "Evidence ingestion completed",
                extra={
                    "case_id": str(case_id),
                    "evidence_id": str(evidence.id),
                    "file_size": evidence.file_size,
                },
            )
            return EvidenceResponse(
                id=evidence.id,
                case_id=evidence.case_id,
                evidence_number=evidence.evidence_number,
                original_filename=evidence.original_filename,
                stored_filename=evidence.stored_filename,
                mime_type=evidence.mime_type,
                file_size=evidence.file_size,
                sha256_hash=evidence.sha256_hash,
                status=evidence.status,
                metadata=evidence.metadata_json,
                created_at=evidence.created_at,
                updated_at=evidence.updated_at,
                custody_events=[custody_event],
            )
        except Exception:
            await self.session.rollback()
            logger.exception(
                "Evidence ingestion failed",
                extra={
                    "case_id": str(case_id),
                    "evidence_id": str(evidence_id) if evidence_id else None,
                },
            )
            raise
        finally:
            await self._cleanup(temporary_key)
            if final_key is not None and not registered:
                await self._cleanup(final_key)

    async def get(self, evidence_id: UUID) -> EvidenceResponse:
        """Return evidence metadata and custody history."""

        evidence = await self.repository.get(evidence_id)
        if evidence is None:
            raise ResourceNotFoundError("The requested evidence was not found.")
        return EvidenceResponse.model_validate(
            {
                "id": evidence.id,
                "case_id": evidence.case_id,
                "evidence_number": evidence.evidence_number,
                "original_filename": evidence.original_filename,
                "stored_filename": evidence.stored_filename,
                "mime_type": evidence.mime_type,
                "file_size": evidence.file_size,
                "sha256_hash": evidence.sha256_hash,
                "status": evidence.status,
                "metadata": evidence.metadata_json,
                "created_at": evidence.created_at,
                "updated_at": evidence.updated_at,
                "custody_events": [
                    self.custody_service.to_response(event)
                    for event in evidence.custody_events
                ],
            }
        )

    async def list_for_case(
        self,
        case_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> EvidenceListResponse:
        """Return a bounded evidence page after verifying its case."""

        if await self.case_repository.get(case_id) is None:
            raise ResourceNotFoundError("The requested case was not found.")
        evidence_items, total = await self.repository.list_for_case(
            case_id,
            limit=limit,
            offset=offset,
        )
        return EvidenceListResponse(
            items=[
                EvidenceResponse(
                    id=evidence.id,
                    case_id=evidence.case_id,
                    evidence_number=evidence.evidence_number,
                    original_filename=evidence.original_filename,
                    stored_filename=evidence.stored_filename,
                    mime_type=evidence.mime_type,
                    file_size=evidence.file_size,
                    sha256_hash=evidence.sha256_hash,
                    status=evidence.status,
                    metadata=evidence.metadata_json,
                    created_at=evidence.created_at,
                    updated_at=evidence.updated_at,
                )
                for evidence in evidence_items
            ],
            total=total,
        )

    async def _cleanup(self, storage_key: str) -> None:
        """Best-effort cleanup that never hides the ingestion failure."""

        try:
            await self.storage.delete(storage_key)
        except Exception:
            logger.exception("Evidence storage cleanup failed")
