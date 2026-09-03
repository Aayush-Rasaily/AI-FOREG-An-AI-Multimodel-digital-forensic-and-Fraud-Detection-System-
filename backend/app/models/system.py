"""SQLAlchemy persistence for system diagnostics runs."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON, Uuid

from backend.app.infrastructure.database.base import Base


class SystemDiagnosticsRun(Base):
    """Persisted result of one system diagnostics execution."""

    __tablename__ = "system_diagnostics_runs"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4,
    )
    overall_status: Mapped[str] = mapped_column(
        String(32), nullable=False,
    )
    results_json: Mapped[dict[str, Any]] = mapped_column(
        "results", JSON, nullable=False, default=dict,
    )
    engine_version: Mapped[str] = mapped_column(
        String(32), nullable=False,
    )
    policy_version: Mapped[str] = mapped_column(
        String(32), nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
