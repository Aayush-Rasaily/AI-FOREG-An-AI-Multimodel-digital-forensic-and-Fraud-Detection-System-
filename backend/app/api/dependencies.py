"""FastAPI dependency providers for transport-layer composition."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.ai.service import AIService
from backend.app.application.services.case_service import CaseService
from backend.app.application.services.evidence_service import EvidenceService
from backend.app.application.services.file_validation import FileValidationService
from backend.app.application.services.hashing import HashService
from backend.app.application.services.processing_service import (
    ProcessingOrchestrator,
)
from backend.app.application.services.storage import StorageService
from backend.app.comparison.service import ComparisonService
from backend.app.core.config import Settings
from backend.app.core.exceptions import StorageError
from backend.app.extraction.service import ExtractionService
from backend.app.forensics.service import ForensicAnalysisService
from backend.app.infrastructure.database.session import get_db_session
from backend.app.infrastructure.storage.local import LocalStorage

if TYPE_CHECKING:
    from backend.app.ai.audio.service import AudioAnalysisService
    from backend.app.audit.service import AuditService
    from backend.app.collaboration.service import CollaborationService
    from backend.app.intelligence.service import InvestigationIntelligenceService
    from backend.app.system.service import SystemService
    from backend.app.ai.document.service import DocumentAnalysisService
    from backend.app.ai.document.signature.service import SignatureVerificationService
    from backend.app.ai.image.service import ImageAnalysisService
    from backend.app.ai.video.service import VideoAnalysisService
    from backend.app.case_intelligence.service import CaseIntelligenceService
    from backend.app.correlation.service import CorrelationService
    from backend.app.entities.service import EntityService
    from backend.app.fusion.service import FusionService
    from backend.app.reporting.service import ReportService
    from backend.app.timeline.service import TimelineService

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


def get_processing_orchestrator(
    session: SessionDependency,
    storage: Annotated[StorageService, Depends(get_storage_service)],
    hash_service: Annotated[HashService, Depends(get_hash_service)],
    settings: RuntimeSettingsDependency,
) -> ProcessingOrchestrator:
    """Compose the processing orchestrator for one request."""

    return ProcessingOrchestrator(
        session=session,
        storage=storage,
        hash_service=hash_service,
        settings=settings,
    )


def get_extraction_service(
    session: SessionDependency,
    storage: Annotated[StorageService, Depends(get_storage_service)],
    hash_service: Annotated[HashService, Depends(get_hash_service)],
    settings: RuntimeSettingsDependency,
) -> ExtractionService:
    """Compose the extraction service for one request."""

    return ExtractionService(
        session=session,
        storage=storage,
        hash_service=hash_service,
        settings=settings,
    )


def get_forensic_service(
    session: SessionDependency,
    storage: Annotated[StorageService, Depends(get_storage_service)],
    hash_service: Annotated[HashService, Depends(get_hash_service)],
    settings: RuntimeSettingsDependency,
) -> ForensicAnalysisService:
    """Compose the forensic analysis service for one request."""

    return ForensicAnalysisService(
        session=session,
        storage=storage,
        hash_service=hash_service,
        settings=settings,
    )


def get_comparison_service(
    session: SessionDependency,
    storage: Annotated[StorageService, Depends(get_storage_service)],
    hash_service: Annotated[HashService, Depends(get_hash_service)],
    settings: RuntimeSettingsDependency,
) -> ComparisonService:
    """Compose the reference comparison service for one request."""

    return ComparisonService(
        session=session,
        storage=storage,
        hash_service=hash_service,
        settings=settings,
    )


def get_ai_service(session: SessionDependency, request: Request) -> AIService:
    """Compose the AI infrastructure service for one request."""

    stack = request.app.state.ai_stack
    return AIService(
        session=session,
        registry=stack["registry"],
        loader=stack["loader"],
        cache=stack["cache"],
        device_manager=stack["device_manager"],
        engine=stack["engine"],
        settings=stack["settings"],
    )


def get_image_analysis_service(
    session: SessionDependency,
    request: Request,
    storage: Annotated[StorageService, Depends(get_storage_service)],
    hash_service: Annotated[HashService, Depends(get_hash_service)],
    settings: RuntimeSettingsDependency,
) -> ImageAnalysisService:
    """Compose the AI image analysis service for one request."""

    from backend.app.ai.image.service import ImageAnalysisService

    stack = request.app.state.image_ai_stack
    return ImageAnalysisService(
        session=session,
        storage=storage,
        hash_service=hash_service,
        settings=settings,
        engine=stack["engine"],
        image_settings=stack["settings"],
    )


def get_document_analysis_service(
    session: SessionDependency,
    request: Request,
    storage: Annotated[StorageService, Depends(get_storage_service)],
    hash_service: Annotated[HashService, Depends(get_hash_service)],
    settings: RuntimeSettingsDependency,
) -> DocumentAnalysisService:
    """Compose the AI document analysis service for one request."""

    from backend.app.ai.document.service import DocumentAnalysisService

    stack = request.app.state.document_ai_stack
    return DocumentAnalysisService(
        session=session,
        storage=storage,
        hash_service=hash_service,
        settings=settings,
        engine=stack["engine"],
        document_settings=stack["settings"],
    )


def get_signature_verification_service(
    session: SessionDependency,
    storage: Annotated[StorageService, Depends(get_storage_service)],
    hash_service: Annotated[HashService, Depends(get_hash_service)],
    settings: RuntimeSettingsDependency,
) -> SignatureVerificationService:
    """Compose the signature verification service for one request."""

    from backend.app.ai.document.signature.service import SignatureVerificationService

    return SignatureVerificationService(
        session=session,
        storage=storage,
        hash_service=hash_service,
        settings=settings,
    )


def get_video_analysis_service(
    session: SessionDependency,
    request: Request,
    storage: Annotated[StorageService, Depends(get_storage_service)],
    hash_service: Annotated[HashService, Depends(get_hash_service)],
    settings: RuntimeSettingsDependency,
) -> VideoAnalysisService:
    """Compose the AI video analysis service for one request."""

    from backend.app.ai.video.service import VideoAnalysisService

    stack = request.app.state.video_ai_stack
    return VideoAnalysisService(
        session=session,
        storage=storage,
        hash_service=hash_service,
        settings=settings,
        engine=stack["engine"],
        video_settings=stack["settings"],
    )


def get_audio_analysis_service(
    session: SessionDependency,
    request: Request,
    storage: Annotated[StorageService, Depends(get_storage_service)],
    hash_service: Annotated[HashService, Depends(get_hash_service)],
    settings: RuntimeSettingsDependency,
) -> AudioAnalysisService:
    """Compose the AI audio analysis service for one request."""

    from backend.app.ai.audio.service import AudioAnalysisService

    stack = request.app.state.audio_ai_stack
    return AudioAnalysisService(
        session=session,
        storage=storage,
        hash_service=hash_service,
        settings=settings,
        engine=stack["engine"],
        audio_settings=stack["settings"],
    )


def get_fusion_service(
    session: SessionDependency,
    storage: Annotated[StorageService, Depends(get_storage_service)],
    hash_service: Annotated[HashService, Depends(get_hash_service)],
    settings: RuntimeSettingsDependency,
) -> FusionService:
    """Compose the multimodal fusion service for one request."""

    from backend.app.fusion.service import FusionService

    return FusionService(
        session=session,
        storage=storage,
        hash_service=hash_service,
        settings=settings,
    )


def get_case_intelligence_service(
    session: SessionDependency,
    storage: Annotated[StorageService, Depends(get_storage_service)],
    hash_service: Annotated[HashService, Depends(get_hash_service)],
    settings: RuntimeSettingsDependency,
) -> CaseIntelligenceService:
    """Compose the case intelligence service for one request."""

    from backend.app.case_intelligence.service import CaseIntelligenceService

    return CaseIntelligenceService(
        session=session,
        storage=storage,
        hash_service=hash_service,
        settings=settings,
    )


def get_report_service(
    session: SessionDependency,
    storage: Annotated[StorageService, Depends(get_storage_service)],
    hash_service: Annotated[HashService, Depends(get_hash_service)],
    settings: RuntimeSettingsDependency,
) -> ReportService:
    """Compose the forensic report service for one request."""

    from backend.app.reporting.service import ReportService

    return ReportService(
        session=session,
        storage=storage,
        hash_service=hash_service,
        settings=settings,
    )


def get_timeline_service(
    session: SessionDependency,
    storage: Annotated[StorageService, Depends(get_storage_service)],
    hash_service: Annotated[HashService, Depends(get_hash_service)],
    settings: RuntimeSettingsDependency,
) -> TimelineService:
    """Compose the investigation timeline service for one request."""

    from backend.app.timeline.service import TimelineService

    return TimelineService(
        session=session,
        storage=storage,
        hash_service=hash_service,
        settings=settings,
    )


def get_correlation_service(
    session: SessionDependency,
    storage: Annotated[StorageService, Depends(get_storage_service)],
    hash_service: Annotated[HashService, Depends(get_hash_service)],
    settings: RuntimeSettingsDependency,
) -> CorrelationService:
    """Compose the cross-evidence correlation service for one request."""

    from backend.app.correlation.service import CorrelationService

    return CorrelationService(
        session=session,
        storage=storage,
        hash_service=hash_service,
        settings=settings,
    )


def get_entity_service(
    session: SessionDependency,
    storage: Annotated[StorageService, Depends(get_storage_service)],
    hash_service: Annotated[HashService, Depends(get_hash_service)],
    settings: RuntimeSettingsDependency,
) -> EntityService:
    """Compose the entity-resolution service for one request."""

    from backend.app.entities.service import EntityService

    return EntityService(
        session=session,
        storage=storage,
        hash_service=hash_service,
        settings=settings,
    )


def get_audit_service(
    session: SessionDependency,
) -> AuditService:
    """Compose the audit service for one request."""

    from backend.app.audit.service import AuditService

    return AuditService(session=session)


def get_system_service(
    session: SessionDependency,
    settings: RuntimeSettingsDependency,
) -> SystemService:
    """Compose the system administration service for one request."""

    from backend.app.system.service import SystemService

    return SystemService(session=session, settings=settings)


def get_collaboration_service(
    session: SessionDependency,
) -> CollaborationService:
    """Compose the collaboration service for one request."""

    from backend.app.collaboration.service import CollaborationService

    return CollaborationService(session=session)


def get_intelligence_service(
    session: SessionDependency,
) -> InvestigationIntelligenceService:
    """Compose the investigation intelligence service for one request."""

    from backend.app.intelligence.service import (
        InvestigationIntelligenceService,
    )

    return InvestigationIntelligenceService(session=session)


__all__ = [
    "SessionDependency",
    "get_ai_service",
    "get_audit_service",
    "get_case_service",
    "get_collaboration_service",
    "get_intelligence_service",
    "get_comparison_service",
    "get_db_session",
    "get_document_analysis_service",
    "get_evidence_service",
    "get_extraction_service",
    "get_file_validation_service",
    "get_forensic_service",
    "get_hash_service",
    "get_image_analysis_service",
    "get_processing_orchestrator",
    "get_runtime_settings",
    "get_signature_verification_service",
    "get_storage_service",
    "get_system_service",
    "get_video_analysis_service",
    "get_audio_analysis_service",
    "get_fusion_service",
    "get_case_intelligence_service",
    "get_report_service",
    "get_timeline_service",
    "get_correlation_service",
    "get_entity_service",
]
