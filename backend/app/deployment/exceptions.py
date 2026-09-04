"""Deployment domain exceptions."""

from fastapi import status

from backend.app.core.exceptions import ApplicationError


class DeploymentError(ApplicationError):
    """Base deployment / readiness failure."""

    status_code = status.HTTP_400_BAD_REQUEST
    code = "DEPLOYMENT_ERROR"


class ConfigurationInvalidError(ApplicationError):
    """Raised when production configuration fails validation."""

    status_code = status.HTTP_409_CONFLICT
    code = "CONFIGURATION_INVALID"


class ReadinessFailedError(ApplicationError):
    """Raised when readiness checks fail in strict mode."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    code = "READINESS_FAILED"
