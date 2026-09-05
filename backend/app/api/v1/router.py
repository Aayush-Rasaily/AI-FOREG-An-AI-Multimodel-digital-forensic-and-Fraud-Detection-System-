"""Versioned API router composition."""

from fastapi import APIRouter, Depends

from backend.app.api.v1.endpoints.admin import (
    permissions_router,
    roles_router,
    sessions_router,
)
from backend.app.api.v1.endpoints.ai import router as ai_router
from backend.app.api.v1.endpoints.audio_ai import router as audio_ai_router
from backend.app.api.v1.endpoints.audit import router as audit_router
from backend.app.api.v1.endpoints.auth import router as auth_router
from backend.app.api.v1.endpoints.case_intelligence import (
    router as case_intelligence_router,
)
from backend.app.api.v1.endpoints.cases import router as cases_router
from backend.app.api.v1.endpoints.collaboration import (
    router as collaboration_router,
)
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
from backend.app.api.v1.endpoints.intelligence import (
    router as intelligence_router,
)
from backend.app.api.v1.endpoints.interoperability import (
    router as interoperability_router,
)
from backend.app.api.v1.endpoints.decision_support import (
    router as decision_support_router,
)
from backend.app.api.v1.endpoints.case_review import (
    router as case_review_router,
)
from backend.app.api.v1.endpoints.integrity import (
    router as integrity_router,
)
from backend.app.api.v1.endpoints.analytics import (
    router as analytics_router,
)
from backend.app.api.v1.endpoints.platform_validation import (
    router as platform_validation_router,
)
from backend.app.api.v1.endpoints.investigation_intelligence import (
    router as investigation_intelligence_router,
)
from backend.app.api.v1.endpoints.knowledge_graph import (
    router as knowledge_graph_router,
)
from backend.app.api.v1.endpoints.monitoring import (
    router as monitoring_router,
)
from backend.app.api.v1.endpoints.processing import router as processing_router
from backend.app.api.v1.endpoints.reports import router as reports_router
from backend.app.api.v1.endpoints.security import (
    router as security_router,
)
from backend.app.api.v1.endpoints.signature_ai import router as signature_ai_router
from backend.app.api.v1.endpoints.system import router as system_router
from backend.app.api.v1.endpoints.system_admin import (
    router as system_admin_router,
)
from backend.app.api.v1.endpoints.system_release import (
    router as system_release_router,
)
from backend.app.api.v1.endpoints.timeline import router as timeline_router
from backend.app.api.v1.endpoints.users import router as users_router
from backend.app.api.v1.endpoints.video_ai import router as video_ai_router
from backend.app.api.v1.endpoints.workflow import (
    router as workflow_router,
)
from backend.app.auth.middleware import require_request_authorization

router = APIRouter(dependencies=[Depends(require_request_authorization)])
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(roles_router)
router.include_router(permissions_router)
router.include_router(sessions_router)
router.include_router(interoperability_router)
router.include_router(knowledge_graph_router)
router.include_router(investigation_intelligence_router)
router.include_router(decision_support_router)
router.include_router(case_review_router)
router.include_router(integrity_router)
router.include_router(analytics_router)
router.include_router(platform_validation_router)
router.include_router(cases_router)
router.include_router(collaboration_router)
router.include_router(case_intelligence_router)
router.include_router(intelligence_router)
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
router.include_router(system_release_router)
router.include_router(monitoring_router)
router.include_router(workflow_router)
router.include_router(security_router)
router.include_router(audit_router)
