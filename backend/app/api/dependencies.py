"""FastAPI dependency providers for transport-layer composition."""

from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.application.services.case_service import CaseService
from backend.app.application.services.evidence_service import EvidenceService
from backend.app.application.services.file_validation import FileValidationService
from backend.app.application.services.hashing import HashService
from backend.app.application.services.storage import StorageService
from backend.app.core.config import Settings
from backend.app.core.exceptions import StorageError
from backend.app.infrastructure.database.session import get_db_session
from backend.app.infrastructure.storage.local import LocalStorage

SessionDependency = Annotated[AsyncSession, Depends(get_db_session)]


def get_runtime_settings(request: Request) -> Settings:
    """Read the settings belonging to the current application instance."""

    return request.app.state.settings


RuntimeSettingsDependency = Annotated[Settings, Depends(get_runtime_settings)]


def get_storage_service(settings: RuntimeSettingsDependency) -> StorageService:
    """Build the configured storage adapter at the composition boundary."""

    if settings.storage_backend != "local":
        raise StorageError(
            "The configured storage backend is not available in this deployment."
        )
    return LocalStorage(settings.storage_root)


def get_hash_service() -> HashService:
    """Build the stateless streaming hash service."""

    return HashService()


def get_file_validation_service(
    settings: RuntimeSettingsDependency,
) -> FileValidationService:
    """Build the configured upload validation service."""

    return FileValidationService(settings)


def get_case_service(session: SessionDependency) -> CaseService:
    """Compose the case application service for one request."""

    return CaseService(session)


def get_evidence_service(
    session: SessionDependency,
    storage: Annotated[StorageService, Depends(get_storage_service)],
    hash_service: Annotated[HashService, Depends(get_hash_service)],
    validation_service: Annotated[
        FileValidationService,
        Depends(get_file_validation_service),
    ],
    settings: RuntimeSettingsDependency,
) -> EvidenceService:
    """Compose the evidence application service for one request."""

    return EvidenceService(
        session=session,
        storage=storage,
        hash_service=hash_service,
        validation_service=validation_service,
        settings=settings,
    )


__all__ = [
    "SessionDependency",
    "get_case_service",
    "get_db_session",
    "get_evidence_service",
    "get_file_validation_service",
    "get_hash_service",
    "get_runtime_settings",
    "get_storage_service",
]
