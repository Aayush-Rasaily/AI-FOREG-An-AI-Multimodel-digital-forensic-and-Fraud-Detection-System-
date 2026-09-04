"""Application service for production readiness and release checks."""

from __future__ import annotations

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import Settings
from backend.app.deployment.backup import (
    create_configuration_export,
    create_database_backup_metadata,
    create_report_archive_metadata,
    list_backup_metadata,
)
from backend.app.deployment.configuration import (
    configuration_profile,
    export_configuration,
    verify_configuration,
)
from backend.app.deployment.health import liveness_payload
from backend.app.deployment.readiness import readiness_payload
from backend.app.deployment.recovery import (
    validate_restore_readiness,
    verify_disaster_recovery,
)
from backend.app.deployment.release import (
    DEPLOYMENT_ENGINE_VERSION,
    DEPLOYMENT_POLICY_VERSION,
    build_release_metadata,
)
from backend.app.deployment.schemas import (
    ConfigurationResponse,
    LivenessResponse,
    ReadinessResponse,
    ReleaseCheckResponse,
    ReleaseResponse,
    StartupValidationResponse,
    ValidationResponse,
    VersionResponse,
)
from backend.app.deployment.startup import (
    get_startup_validation,
    run_startup_validation,
)
from backend.app.deployment.validation import run_operational_validation


class DeploymentService:
    """Compose production readiness and release operations."""

    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings

    def get_version(self) -> VersionResponse:
        return VersionResponse(
            application_version=self.settings.app_version,
            service=self.settings.app_name,
            environment=self.settings.app_env,
            policy_version=DEPLOYMENT_POLICY_VERSION,
            engine_version=DEPLOYMENT_ENGINE_VERSION,
        )

    def get_release(self, request: Request | None = None) -> ReleaseResponse:
        state = request.app.state if request is not None else None
        meta = build_release_metadata(
            app_version=self.settings.app_version,
            environment=self.settings.app_env,
            app_state=state,
        )
        return ReleaseResponse(**meta)

    def get_liveness(self) -> LivenessResponse:
        return LivenessResponse(**liveness_payload(self.settings))

    async def get_readiness(
        self, request: Request | None = None,
    ) -> ReadinessResponse:
        state = request.app.state if request is not None else None
        payload = await readiness_payload(
            settings=self.settings,
            session=self.session,
            app_state=state,
        )
        return ReadinessResponse(**payload)

    def get_startup_validation(self) -> StartupValidationResponse:
        result = get_startup_validation()
        if result is None:
            result = run_startup_validation(self.settings)
        return StartupValidationResponse(**result)

    def get_configuration(self) -> ConfigurationResponse:
        return ConfigurationResponse(
            profile=configuration_profile(self.settings),
            export=export_configuration(self.settings),
            findings=verify_configuration(self.settings),
        )

    async def validate(
        self, request: Request | None = None,
    ) -> ValidationResponse:
        state = request.app.state if request is not None else None
        result = await run_operational_validation(
            settings=self.settings,
            session=self.session,
            app_state=state,
        )
        return ValidationResponse(**result)

    async def release_check(
        self, request: Request | None = None,
    ) -> ReleaseCheckResponse:
        # Ensure backup metadata exists for DR verification path
        create_database_backup_metadata(self.settings)
        create_report_archive_metadata(self.settings)
        create_configuration_export(self.settings)

        validation = await self.validate(request)
        release = self.get_release(request)
        dr = verify_disaster_recovery(self.settings)
        restore = validate_restore_readiness(self.settings)
        backups = list_backup_metadata(self.settings)

        status = "PASSED"
        if validation.status == "FAILED" or restore["status"] != "READY":
            status = "FAILED" if validation.status == "FAILED" else "DEGRADED"

        return ReleaseCheckResponse(
            status=status,
            release=release,
            validation=validation,
            disaster_recovery=dr,
            restore=restore,
            backup_records=backups,
        )
