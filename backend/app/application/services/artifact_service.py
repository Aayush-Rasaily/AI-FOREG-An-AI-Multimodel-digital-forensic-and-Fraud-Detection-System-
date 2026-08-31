"""Application service for independently stored derived artifacts."""

import logging
from io import BytesIO
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.application.processors.base import DerivedArtifactPayload
from backend.app.application.services.hashing import HashService
from backend.app.application.services.storage import StorageService
from backend.app.core.config import Settings
from backend.app.infrastructure.database.repositories.processing import (
    ArtifactRepository,
)
from backend.app.models.evidence import Evidence
from backend.app.models.processing import Artifact

logger = logging.getLogger(__name__)


class ArtifactService:
    """Hash, store, and stage derived artifacts without touching originals."""

    def __init__(
        self,
        session: AsyncSession,
        storage: StorageService,
        hash_service: HashService,
        settings: Settings,
    ) -> None:
        self.session = session
        self.storage = storage
        self.hash_service = hash_service
        self.settings = settings
        self.repository = ArtifactRepository(session)

    async def create(
        self,
        evidence: Evidence,
        payload: DerivedArtifactPayload,
    ) -> Artifact:
        """Persist one independently hashed artifact and stage its database row."""

        artifact_id = uuid4()
        temporary_key = self.storage.temporary_key()
        storage_key = self.storage.artifact_key(
            evidence.case_id,
            evidence.id,
            artifact_id,
        )
        committed = False
        try:
            await self.storage.save_stream(
                BytesIO(payload.content),
                temporary_key,
                max_bytes=self.settings.max_upload_size_mb * 1024 * 1024,
                chunk_size=self.settings.upload_chunk_size_bytes,
            )
            async with self.storage.open(temporary_key) as stream:
                hash_result = await self.hash_service.hash_stream(
                    stream,
                    chunk_size=self.settings.upload_chunk_size_bytes,
                )
            await self.storage.commit(temporary_key, storage_key)
            committed = True
            artifact = Artifact(
                id=artifact_id,
                evidence_id=evidence.id,
                artifact_type=payload.artifact_type,
                storage_key=storage_key,
                mime_type=payload.mime_type,
                file_size=hash_result.file_size,
                sha256_hash=hash_result.sha256_hash,
                metadata_json=payload.metadata,
            )
            await self.repository.add(artifact)
            logger.info(
                "Artifact created",
                extra={
                    "evidence_id": str(evidence.id),
                    "artifact_id": str(artifact.id),
                    "artifact_type": artifact.artifact_type.value,
                },
            )
            return artifact
        except Exception:
            if committed:
                await self._cleanup(storage_key)
            raise
        finally:
            await self._cleanup(temporary_key)

    async def cleanup(self, artifact: Artifact) -> None:
        """Remove a newly-created artifact during a failed job transaction."""

        await self._cleanup(artifact.storage_key)

    async def _cleanup(self, storage_key: str) -> None:
        """Best-effort cleanup that preserves the original exception."""

        try:
            await self.storage.delete(storage_key)
        except Exception:
            logger.exception("Artifact storage cleanup failed")
