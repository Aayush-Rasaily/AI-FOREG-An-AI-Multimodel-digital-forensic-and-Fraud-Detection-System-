"""Versioned API router composition."""

from fastapi import APIRouter

from backend.app.api.v1.endpoints.ai import router as ai_router
from backend.app.api.v1.endpoints.audit import router as audit_router
from backend.app.api.v1.endpoints.audio_ai import router as audio_ai_router
from backend.app.api.v1.endpoints.case_intelligence import (
    router as case_intelligence_router,
)
from backend.app.api.v1.endpoints.cases import router as cases_router
from backend.app.api.v1.endpoints.comparison import router as comparison_router
from backend.app.api.v1.endpoints.correlation import router as correlation_router
from backend.app.api.v1.endpoints.document_ai import router as document_ai_router
from backend.app.api.v1.endpoints.entities import router as entities_router
from backend.app.api.v1.endpoints.evidence import router as evidence_router
from backend.app.api.v1.endpoints.extraction import router as extraction_router
from backend.app.api.v1.endpoints.forensics import router as forensics_router
from backend.app.api.v1.endpoints.fusion import router as fusion_router
from backend.app.api.v1.endpoints.health import router as health_router
from backend.app.api.v1.endpoints.image_ai import router as image_ai_router
from backend.app.api.v1.endpoints.processing import router as processing_router
from backend.app.api.v1.endpoints.reports import router as reports_router
from backend.app.api.v1.endpoints.signature_ai import router as signature_ai_router
from backend.app.api.v1.endpoints.system import router as system_router
from backend.app.api.v1.endpoints.system_admin import (
    router as system_admin_router,
)
from backend.app.api.v1.endpoints.timeline import router as timeline_router
from backend.app.api.v1.endpoints.video_ai import router as video_ai_router

router = APIRouter()
router.include_router(health_router)
router.include_router(cases_router)
router.include_router(case_intelligence_router)
router.include_router(reports_router)
router.include_router(timeline_router)
router.include_router(correlation_router)
router.include_router(entities_router)
router.include_router(evidence_router)
router.include_router(extraction_router)
router.include_router(forensics_router)
router.include_router(comparison_router)
router.include_router(ai_router)
router.include_router(image_ai_router)
router.include_router(document_ai_router)
router.include_router(signature_ai_router)
router.include_router(video_ai_router)
router.include_router(audio_ai_router)
router.include_router(fusion_router)
router.include_router(processing_router)
router.include_router(system_router)
router.include_router(system_admin_router)
router.include_router(audit_router)
