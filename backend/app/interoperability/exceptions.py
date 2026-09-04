"""Interoperability domain exceptions."""

from fastapi import status

from backend.app.core.exceptions import ApplicationError


class InteropError(ApplicationError):
    """Base interoperability failure."""

    status_code = status.HTTP_400_BAD_REQUEST
    code = "INTEROP_ERROR"


class PackageValidationError(ApplicationError):
    """Raised when an import package fails validation."""

    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    code = "PACKAGE_VALIDATION_FAILED"


class PackageConflictError(ApplicationError):
    """Raised when import would overwrite an existing investigation."""

    status_code = status.HTTP_409_CONFLICT
    code = "PACKAGE_CONFLICT"


class ExportNotFoundError(ApplicationError):
    """Raised when an export job cannot be located."""

    status_code = status.HTTP_404_NOT_FOUND
    code = "EXPORT_NOT_FOUND"


class ImportNotFoundError(ApplicationError):
    """Raised when an import job cannot be located."""

    status_code = status.HTTP_404_NOT_FOUND
    code = "IMPORT_NOT_FOUND"


class UnsupportedFormatError(ApplicationError):
    """Raised when an export format is not supported."""

    status_code = status.HTTP_400_BAD_REQUEST
    code = "UNSUPPORTED_EXPORT_FORMAT"
