"""Versioned API router composition."""

from fastapi import APIRouter

from backend.app.api.v1.endpoints.cases import router as cases_router
from backend.app.api.v1.endpoints.evidence import router as evidence_router
from backend.app.api.v1.endpoints.health import router as health_router
from backend.app.api.v1.endpoints.processing import router as processing_router
from backend.app.api.v1.endpoints.system import router as system_router

router = APIRouter()
router.include_router(health_router)
router.include_router(cases_router)
router.include_router(evidence_router)
router.include_router(processing_router)
router.include_router(system_router)
