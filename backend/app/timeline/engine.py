"""Investigation timeline reconstruction engine."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.audio_ai import AudioAnalysisRun
from backend.app.models.case import Case
from backend.app.models.case_intelligence import CaseIntelligenceRun
from backend.app.models.custody import ChainOfCustodyEvent
from backend.app.models.document_ai import DocumentAnalysisRun
from backend.app.models.evidence import Evidence
from backend.app.models.extraction import ExtractionRecord
from backend.app.models.forensic_report import ForensicReport
from backend.app.models.forensics import AnalysisRun
from backend.app.models.fusion import FusionAnalysisRun
from backend.app.models.image_ai import ImageAnalysisRun
from backend.app.models.processing import ProcessingJob
from backend.app.models.signature_ai import SignatureVerificationRun
from backend.app.models.video_ai import VideoAnalysisRun
from backend.app.timeline.confidence import uncertainty_ms
from backend.app.timeline.models import (
    TimelineBuildResult,
    TimelineConflict,
    TimelineConflictType,
    TimelineEvent,
    TimelineEventType,
)
from backend.app.timeline.normalization import (
    normalize_metadata_timestamp,
    normalize_timestamp,
)
from backend.app.timeline.ordering import order_events
from backend.app.timeline.policy import ENGINE_VERSION, POLICY_VERSION
from backend.app.timeline.provenance import build_provenance


class TimelineEngine:
    """Collect and normalize chronological investigation events."""

    async def build(
        self,
        session: AsyncSession,
        case: Case,
    ) -> TimelineBuildResult:
        """Build a deterministic timeline from persisted case data."""

        events: list[TimelineEvent] = []
        evidence_rows = list(
            await session.scalars(select(Evidence).where(Evidence.case_id == case.id))
        )
        evidence_ids = [item.id for item in evidence_rows]

        for evidence in evidence_rows:
            events.extend(self._evidence_events(case.id, evidence))
            events.extend(await self._metadata_events(case.id, evidence))
            events.extend(await self._missing_timestamp_events(case.id, evidence))

        if evidence_ids:
            events.extend(await self._processing_events(session, case.id, evidence_ids))
            events.extend(await self._extraction_events(session, case.id, evidence_ids))
            events.extend(await self._custody_events(session, case.id, evidence_ids))
            events.extend(await self._forensic_events(session, case.id, evidence_ids))
            events.extend(await self._image_ai_events(session, case.id, evidence_ids))
            events.extend(
                await self._document_ai_events(session, case.id, evidence_ids)
            )
            events.extend(
                await self._signature_ai_events(session, case.id, evidence_ids)
            )
            events.extend(await self._video_ai_events(session, case.id, evidence_ids))
            events.extend(await self._audio_ai_events(session, case.id, evidence_ids))
            events.extend(await self._fusion_events(session, case.id, evidence_ids))

        events.extend(await self._case_intelligence_events(session, case.id))
        events.extend(await self._report_events(session, case.id))

        ordered = order_events(events)
        conflicts = self._detect_conflicts(ordered)
        provenance = build_provenance(
            case_id=case.id,
            case_number=case.case_number,
        )
        return TimelineBuildResult(
            events=ordered,
            conflicts=conflicts,
            provenance={
                **provenance,
                "engine_version": ENGINE_VERSION,
                "policy_version": POLICY_VERSION,
                "evidence_count": len(evidence_rows),
            },
            metadata={
                "event_count": len(ordered),
                "conflict_count": len(conflicts),
                "evidence_count": len(evidence_rows),
            },
        )

    def _evidence_events(
        self, case_id: UUID, evidence: Evidence
    ) -> list[TimelineEvent]:
        events: list[TimelineEvent] = []
        uploaded = normalize_timestamp(evidence.created_at, source="filesystem")
        events.append(
            self._event(
                event_id=f"evidence_uploaded:{evidence.id}",
                case_id=case_id,
                evidence_id=evidence.id,
                event_type=TimelineEventType.EVIDENCE_UPLOADED,
                normalized=uploaded,
                description=f"Evidence {evidence.evidence_number} uploaded.",
                source="evidence",
                source_id=str(evidence.id),
                provenance=build_provenance(
                    evidence_id=evidence.id,
                    sha256_hash=evidence.sha256_hash,
                ),
                supporting_artifacts=[evidence.storage_key],
            )
        )
        if evidence.updated_at != evidence.created_at:
            updated = normalize_timestamp(evidence.updated_at, source="filesystem")
            events.append(
                self._event(
                    event_id=f"evidence_updated:{evidence.id}",
                    case_id=case_id,
                    evidence_id=evidence.id,
                    event_type=TimelineEventType.EVIDENCE_UPDATED,
                    normalized=updated,
                    description=(
                        f"Evidence {evidence.evidence_number} metadata updated."
                    ),
                    source="evidence",
                    source_id=str(evidence.id),
                    provenance=build_provenance(evidence_id=evidence.id),
                )
            )
        return events

    async def _metadata_events(
        self,
        case_id: UUID,
        evidence: Evidence,
    ) -> list[TimelineEvent]:
        events: list[TimelineEvent] = []
        metadata = (
            evidence.metadata_json if isinstance(evidence.metadata_json, dict) else {}
        )
        extraction = metadata.get("extraction")
        if isinstance(extraction, dict):
            normalized = normalize_metadata_timestamp(
                extraction,
                keys=("created_at", "modified_at", "document_date", "timestamp"),
                source="signed_document",
            )
            if normalized is not None and normalized.normalized_timestamp is not None:
                events.append(
                    self._event(
                        event_id=f"metadata_document:{evidence.id}",
                        case_id=case_id,
                        evidence_id=evidence.id,
                        event_type=TimelineEventType.METADATA_TIMESTAMP,
                        normalized=normalized,
                        description=(
                            "Document timestamp extracted for "
                            f"{evidence.evidence_number}."
                        ),
                        source="metadata",
                        source_id=f"metadata:extraction:{evidence.id}",
                        provenance=build_provenance(evidence_id=evidence.id),
                        metadata={"metadata_key": "extraction"},
                    )
                )
        exif = metadata.get("exif")
        if isinstance(exif, dict):
            normalized = normalize_metadata_timestamp(
                exif,
                keys=("DateTimeOriginal", "CreateDate", "ModifyDate", "datetime"),
                source="exif",
            )
            if normalized is not None and normalized.normalized_timestamp is not None:
                events.append(
                    self._event(
                        event_id=f"metadata_exif:{evidence.id}",
                        case_id=case_id,
                        evidence_id=evidence.id,
                        event_type=TimelineEventType.METADATA_TIMESTAMP,
                        normalized=normalized,
                        description=(
                            "EXIF timestamp extracted for "
                            f"{evidence.evidence_number}."
                        ),
                        source="metadata",
                        source_id=f"metadata:exif:{evidence.id}",
                        provenance=build_provenance(evidence_id=evidence.id),
                        metadata={"metadata_key": "exif"},
                    )
                )
        filesystem = metadata.get("filesystem")
        if isinstance(filesystem, dict):
            normalized = normalize_metadata_timestamp(
                filesystem,
                keys=("created_at", "modified_at", "accessed_at"),
                source="filesystem",
            )
            if normalized is not None and normalized.normalized_timestamp is not None:
                events.append(
                    self._event(
                        event_id=f"metadata_filesystem:{evidence.id}",
                        case_id=case_id,
                        evidence_id=evidence.id,
                        event_type=TimelineEventType.METADATA_TIMESTAMP,
                        normalized=normalized,
                        description=(
                            "Filesystem timestamp extracted for "
                            f"{evidence.evidence_number}."
                        ),
                        source="metadata",
                        source_id=f"metadata:filesystem:{evidence.id}",
                        provenance=build_provenance(evidence_id=evidence.id),
                        metadata={"metadata_key": "filesystem"},
                    )
                )
        return events

    async def _missing_timestamp_events(
        self,
        case_id: UUID,
        evidence: Evidence,
    ) -> list[TimelineEvent]:
        metadata = (
            evidence.metadata_json if isinstance(evidence.metadata_json, dict) else {}
        )
        mime = evidence.mime_type.lower()
        missing_reason: str | None = None
        if mime.startswith("image/") and not metadata.get("exif"):
            missing_reason = "image missing EXIF datetime"
        elif mime.startswith("video/") and not any(
            metadata.get(key) for key in ("video", "exif", "recording_date")
        ):
            missing_reason = "video missing recording date"
        elif mime.startswith("application/") and not metadata.get("extraction"):
            missing_reason = "document missing creation date"
        if missing_reason is None:
            return []
        normalized = normalize_timestamp(None, source="missing")
        return [
            self._event(
                event_id=f"timestamp_missing:{evidence.id}",
                case_id=case_id,
                evidence_id=evidence.id,
                event_type=TimelineEventType.TIMESTAMP_MISSING,
                normalized=normalized,
                description=missing_reason,
                source="missing",
                source_id=f"missing:{evidence.id}",
                provenance=build_provenance(evidence_id=evidence.id),
                metadata={"reason": missing_reason},
            )
        ]

    async def _processing_events(
        self,
        session: AsyncSession,
        case_id: UUID,
        evidence_ids: list[UUID],
    ) -> list[TimelineEvent]:
        rows = list(
            await session.scalars(
                select(ProcessingJob).where(ProcessingJob.evidence_id.in_(evidence_ids))
            )
        )
        events: list[TimelineEvent] = []
        for job in rows:
            for event_type, timestamp, suffix in (
                (TimelineEventType.PROCESSING_QUEUED, job.created_at, "queued"),
                (TimelineEventType.PROCESSING_STARTED, job.started_at, "started"),
                (TimelineEventType.PROCESSING_COMPLETED, job.completed_at, "completed"),
            ):
                if timestamp is None:
                    continue
                normalized = normalize_timestamp(timestamp, source="processing")
                events.append(
                    self._event(
                        event_id=f"processing_{suffix}:{job.id}",
                        case_id=case_id,
                        evidence_id=job.evidence_id,
                        event_type=event_type,
                        normalized=normalized,
                        description=f"Processing job {job.job_type.value} {suffix}.",
                        source="processing",
                        source_id=str(job.id),
                        provenance=build_provenance(
                            evidence_id=job.evidence_id,
                            processing_job_id=job.id,
                        ),
                        metadata={
                            "job_type": job.job_type.value,
                            "status": job.status.value,
                        },
                    )
                )
        return events

    async def _extraction_events(
        self,
        session: AsyncSession,
        case_id: UUID,
        evidence_ids: list[UUID],
    ) -> list[TimelineEvent]:
        rows = list(
            await session.scalars(
                select(ExtractionRecord).where(
                    ExtractionRecord.evidence_id.in_(evidence_ids)
                )
            )
        )
        events: list[TimelineEvent] = []
        for record in rows:
            normalized = normalize_timestamp(record.created_at, source="processing")
            events.append(
                self._event(
                    event_id=f"extraction:{record.id}",
                    case_id=case_id,
                    evidence_id=record.evidence_id,
                    event_type=TimelineEventType.EXTRACTION_COMPLETED,
                    normalized=normalized,
                    description=(
                        f"Extraction completed ({record.extraction_type.value})."
                    ),
                    source="extraction",
                    source_id=str(record.id),
                    provenance=build_provenance(
                        evidence_id=record.evidence_id,
                        extraction_id=record.id,
                        artifact_id=record.artifact_id,
                    ),
                    metadata={
                        "extraction_type": record.extraction_type.value,
                        "method": record.method,
                    },
                )
            )
        return events

    async def _custody_events(
        self,
        session: AsyncSession,
        case_id: UUID,
        evidence_ids: list[UUID],
    ) -> list[TimelineEvent]:
        rows = list(
            await session.scalars(
                select(ChainOfCustodyEvent).where(
                    ChainOfCustodyEvent.evidence_id.in_(evidence_ids)
                )
            )
        )
        events: list[TimelineEvent] = []
        for custody in rows:
            normalized = normalize_timestamp(custody.timestamp, source="custody")
            events.append(
                self._event(
                    event_id=f"custody:{custody.id}",
                    case_id=case_id,
                    evidence_id=custody.evidence_id,
                    event_type=TimelineEventType.CUSTODY_EVENT,
                    normalized=normalized,
                    description=f"Chain of custody: {custody.event_type.value}.",
                    source="custody",
                    source_id=str(custody.id),
                    provenance=build_provenance(
                        evidence_id=custody.evidence_id,
                        custody_event_id=custody.id,
                    ),
                    metadata=custody.metadata_json,
                )
            )
        return events

    async def _forensic_events(
        self,
        session: AsyncSession,
        case_id: UUID,
        evidence_ids: list[UUID],
    ) -> list[TimelineEvent]:
        rows = list(
            await session.scalars(
                select(AnalysisRun).where(AnalysisRun.evidence_id.in_(evidence_ids))
            )
        )
        return self._analysis_run_events(
            case_id,
            rows,
            event_type=TimelineEventType.FORENSIC_ANALYSIS_COMPLETED,
            source="forensic",
            id_prefix="forensic",
        )

    async def _image_ai_events(
        self,
        session: AsyncSession,
        case_id: UUID,
        evidence_ids: list[UUID],
    ) -> list[TimelineEvent]:
        rows = list(
            await session.scalars(
                select(ImageAnalysisRun).where(
                    ImageAnalysisRun.evidence_id.in_(evidence_ids)
                )
            )
        )
        return self._analysis_run_events(
            case_id,
            rows,
            event_type=TimelineEventType.IMAGE_AI_COMPLETED,
            source="image_ai",
            id_prefix="image_ai",
        )

    async def _document_ai_events(
        self,
        session: AsyncSession,
        case_id: UUID,
        evidence_ids: list[UUID],
    ) -> list[TimelineEvent]:
        rows = list(
            await session.scalars(
                select(DocumentAnalysisRun).where(
                    DocumentAnalysisRun.evidence_id.in_(evidence_ids)
                )
            )
        )
        return self._analysis_run_events(
            case_id,
            rows,
            event_type=TimelineEventType.DOCUMENT_AI_COMPLETED,
            source="document_ai",
            id_prefix="document_ai",
        )

    async def _signature_ai_events(
        self,
        session: AsyncSession,
        case_id: UUID,
        evidence_ids: list[UUID],
    ) -> list[TimelineEvent]:
        rows = list(
            await session.scalars(
                select(SignatureVerificationRun).where(
                    SignatureVerificationRun.questioned_evidence_id.in_(evidence_ids)
                    | SignatureVerificationRun.reference_evidence_id.in_(evidence_ids)
                )
            )
        )
        events: list[TimelineEvent] = []
        for run in rows:
            evidence_id = run.questioned_evidence_id or run.reference_evidence_id
            normalized = normalize_timestamp(run.created_at, source="signature_ai")
            events.append(
                self._event(
                    event_id=f"signature_ai:{run.id}",
                    case_id=case_id,
                    evidence_id=evidence_id,
                    event_type=TimelineEventType.SIGNATURE_AI_COMPLETED,
                    normalized=normalized,
                    description="Signature Ai analysis completed.",
                    source="signature_ai",
                    source_id=str(run.id),
                    provenance=build_provenance(
                        evidence_id=evidence_id,
                        analysis_run_id=run.id,
                        processing_job_id=run.processing_job_id,
                    ),
                    metadata={"verdict": run.verdict.value},
                )
            )
        return events

    async def _video_ai_events(
        self,
        session: AsyncSession,
        case_id: UUID,
        evidence_ids: list[UUID],
    ) -> list[TimelineEvent]:
        rows = list(
            await session.scalars(
                select(VideoAnalysisRun).where(
                    VideoAnalysisRun.evidence_id.in_(evidence_ids)
                )
            )
        )
        return self._analysis_run_events(
            case_id,
            rows,
            event_type=TimelineEventType.VIDEO_AI_COMPLETED,
            source="video_ai",
            id_prefix="video_ai",
        )

    async def _audio_ai_events(
        self,
        session: AsyncSession,
        case_id: UUID,
        evidence_ids: list[UUID],
    ) -> list[TimelineEvent]:
        rows = list(
            await session.scalars(
                select(AudioAnalysisRun).where(
                    AudioAnalysisRun.evidence_id.in_(evidence_ids)
                )
            )
        )
        return self._analysis_run_events(
            case_id,
            rows,
            event_type=TimelineEventType.AUDIO_AI_COMPLETED,
            source="audio_ai",
            id_prefix="audio_ai",
        )

    async def _fusion_events(
        self,
        session: AsyncSession,
        case_id: UUID,
        evidence_ids: list[UUID],
    ) -> list[TimelineEvent]:
        rows = list(
            await session.scalars(
                select(FusionAnalysisRun).where(
                    FusionAnalysisRun.evidence_id.in_(evidence_ids)
                )
            )
        )
        events: list[TimelineEvent] = []
        for run in rows:
            timestamp = run.completed_at or run.started_at or run.created_at
            normalized = normalize_timestamp(timestamp, source="fusion")
            events.append(
                self._event(
                    event_id=f"fusion:{run.id}",
                    case_id=case_id,
                    evidence_id=run.evidence_id,
                    event_type=TimelineEventType.FUSION_COMPLETED,
                    normalized=normalized,
                    description="Phase 6F multimodal fusion completed.",
                    source="fusion",
                    source_id=str(run.id),
                    provenance=build_provenance(
                        evidence_id=run.evidence_id,
                        fusion_run_id=run.id,
                        processing_job_id=run.processing_job_id,
                    ),
                    metadata={
                        "verdict": run.verdict.value if run.verdict else None,
                        "status": run.status.value,
                    },
                )
            )
        return events

    async def _case_intelligence_events(
        self,
        session: AsyncSession,
        case_id: UUID,
    ) -> list[TimelineEvent]:
        rows = list(
            await session.scalars(
                select(CaseIntelligenceRun).where(
                    CaseIntelligenceRun.case_id == case_id
                )
            )
        )
        events: list[TimelineEvent] = []
        for run in rows:
            timestamp = run.completed_at or run.started_at or run.created_at
            normalized = normalize_timestamp(timestamp, source="case_intelligence")
            events.append(
                self._event(
                    event_id=f"case_intelligence:{run.id}",
                    case_id=case_id,
                    evidence_id=None,
                    event_type=TimelineEventType.CASE_INTELLIGENCE_COMPLETED,
                    normalized=normalized,
                    description="Phase 6G case intelligence synthesis completed.",
                    source="case_intelligence",
                    source_id=str(run.id),
                    provenance=build_provenance(
                        case_intelligence_run_id=run.id,
                    ),
                    metadata={"status": run.status.value},
                )
            )
        return events

    async def _report_events(
        self,
        session: AsyncSession,
        case_id: UUID,
    ) -> list[TimelineEvent]:
        rows = list(
            await session.scalars(
                select(ForensicReport).where(ForensicReport.case_id == case_id)
            )
        )
        events: list[TimelineEvent] = []
        for report in rows:
            timestamp = report.completed_at or report.started_at or report.created_at
            normalized = normalize_timestamp(timestamp, source="report")
            if report.completed_at is None and report.status.value != "COMPLETED":
                events.append(
                    self._event(
                        event_id=f"timestamp_missing:report:{report.id}",
                        case_id=case_id,
                        evidence_id=None,
                        event_type=TimelineEventType.TIMESTAMP_MISSING,
                        normalized=normalize_timestamp(None, source="missing"),
                        description="Report missing generation timestamp.",
                        source="missing",
                        source_id=str(report.id),
                        provenance=build_provenance(report_id=report.id),
                        metadata={"report_status": report.status.value},
                    )
                )
                continue
            events.append(
                self._event(
                    event_id=f"report:{report.id}",
                    case_id=case_id,
                    evidence_id=None,
                    event_type=TimelineEventType.REPORT_GENERATED,
                    normalized=normalized,
                    description="Phase 6H forensic report generated.",
                    source="report",
                    source_id=str(report.id),
                    provenance=build_provenance(
                        report_id=report.id,
                        case_intelligence_run_id=report.case_intelligence_run_id,
                    ),
                    metadata={"status": report.status.value},
                )
            )
        return events

    def _analysis_run_events(
        self,
        case_id: UUID,
        rows: list[Any],
        *,
        event_type: TimelineEventType,
        source: str,
        id_prefix: str,
    ) -> list[TimelineEvent]:
        events: list[TimelineEvent] = []
        for run in rows:
            timestamp = (
                getattr(run, "completed_at", None)
                or getattr(run, "started_at", None)
                or getattr(run, "created_at", None)
            )
            normalized = normalize_timestamp(timestamp, source=source)
            events.append(
                self._event(
                    event_id=f"{id_prefix}:{run.id}",
                    case_id=case_id,
                    evidence_id=run.evidence_id,
                    event_type=event_type,
                    normalized=normalized,
                    description=(
                        f"{source.replace('_', ' ').title()} analysis completed."
                    ),
                    source=source,
                    source_id=str(run.id),
                    provenance=build_provenance(
                        evidence_id=run.evidence_id,
                        analysis_run_id=run.id,
                        processing_job_id=getattr(run, "processing_job_id", None),
                    ),
                    metadata={"status": run.status.value},
                )
            )
        return events

    def _detect_conflicts(
        self,
        events: tuple[TimelineEvent, ...],
    ) -> tuple[TimelineConflict, ...]:
        conflicts: list[TimelineConflict] = []
        seen_ids: set[str] = set()
        for event in events:
            if event.event_id in seen_ids:
                conflicts.append(
                    TimelineConflict(
                        conflict_id=f"duplicate:{event.event_id}",
                        conflict_type=TimelineConflictType.DUPLICATE_EVENT,
                        evidence_id=event.evidence_id,
                        involved_event_ids=(event.event_id,),
                        explanation=(
                            f"Duplicate timeline event detected: {event.event_id}."
                        ),
                    )
                )
            seen_ids.add(event.event_id)

        now = datetime.now(UTC)
        for event in events:
            if (
                event.normalized_timestamp
                and event.normalized_timestamp > now + timedelta(minutes=5)
            ):
                conflicts.append(
                    TimelineConflict(
                        conflict_id=f"future:{event.event_id}",
                        conflict_type=TimelineConflictType.FUTURE_TIMESTAMP,
                        evidence_id=event.evidence_id,
                        involved_event_ids=(event.event_id,),
                        explanation="Event timestamp is in the future.",
                        metadata={"timestamp": event.normalized_timestamp.isoformat()},
                    )
                )

        by_evidence: dict[UUID, list[TimelineEvent]] = {}
        for event in events:
            if event.evidence_id is None or event.normalized_timestamp is None:
                continue
            by_evidence.setdefault(event.evidence_id, []).append(event)

        for evidence_id, evidence_events in by_evidence.items():
            metadata_events = [
                item
                for item in evidence_events
                if item.event_type == TimelineEventType.METADATA_TIMESTAMP
            ]
            if len(metadata_events) > 1:
                conflicts.append(
                    TimelineConflict(
                        conflict_id=f"multi_ts:{evidence_id}",
                        conflict_type=TimelineConflictType.MULTIPLE_TIMESTAMPS,
                        evidence_id=evidence_id,
                        involved_event_ids=tuple(
                            item.event_id for item in metadata_events
                        ),
                        explanation=(
                            "Multiple metadata timestamps exist for one artifact."
                        ),
                    )
                )
            filesystem = next(
                (
                    item
                    for item in metadata_events
                    if item.metadata.get("metadata_key") == "filesystem"
                ),
                None,
            )
            exif = next(
                (
                    item
                    for item in metadata_events
                    if item.metadata.get("metadata_key") == "exif"
                ),
                None,
            )
            if (
                filesystem
                and exif
                and filesystem.normalized_timestamp
                and exif.normalized_timestamp
                and filesystem.normalized_timestamp < exif.normalized_timestamp
            ):
                conflicts.append(
                    TimelineConflict(
                        conflict_id=f"fs_before_exif:{evidence_id}",
                        conflict_type=TimelineConflictType.FILESYSTEM_BEFORE_EXIF,
                        evidence_id=evidence_id,
                        involved_event_ids=(filesystem.event_id, exif.event_id),
                        explanation="Filesystem timestamp precedes EXIF capture time.",
                    )
                )
            timezones = {
                item.timezone for item in evidence_events if item.timezone is not None
            }
            if len(timezones) > 1:
                conflicts.append(
                    TimelineConflict(
                        conflict_id=f"tz_mismatch:{evidence_id}",
                        conflict_type=TimelineConflictType.TIMEZONE_MISMATCH,
                        evidence_id=evidence_id,
                        involved_event_ids=tuple(
                            item.event_id for item in evidence_events
                        ),
                        explanation=(
                            "Conflicting timezones detected across evidence events."
                        ),
                        metadata={"timezones": sorted(timezones)},
                    )
                )
            drift_candidates = [
                item
                for item in evidence_events
                if item.normalized_timestamp is not None
            ]
            if len(drift_candidates) >= 2:
                earliest = min(
                    drift_candidates, key=lambda item: item.normalized_timestamp or now
                )
                latest = max(
                    drift_candidates, key=lambda item: item.normalized_timestamp or now
                )
                if (
                    earliest.normalized_timestamp
                    and latest.normalized_timestamp
                    and (latest.normalized_timestamp - earliest.normalized_timestamp)
                    > timedelta(days=365 * 50)
                ):
                    conflicts.append(
                        TimelineConflict(
                            conflict_id=f"clock_drift:{evidence_id}",
                            conflict_type=TimelineConflictType.CLOCK_DRIFT,
                            evidence_id=evidence_id,
                            involved_event_ids=(earliest.event_id, latest.event_id),
                            explanation=(
                                "Extreme timestamp spread suggests clock drift."
                            ),
                        )
                    )
        return tuple(
            sorted(
                conflicts, key=lambda item: (item.conflict_type.value, item.conflict_id)
            )
        )

    @staticmethod
    def _event(
        *,
        event_id: str,
        case_id: UUID,
        evidence_id: UUID | None,
        event_type: TimelineEventType,
        normalized: Any,
        description: str,
        source: str,
        source_id: str,
        provenance: dict[str, Any],
        metadata: dict[str, Any] | None = None,
        supporting_artifacts: list[str] | None = None,
    ) -> TimelineEvent:
        return TimelineEvent(
            event_id=event_id,
            case_id=case_id,
            evidence_id=evidence_id,
            event_type=event_type,
            timestamp=normalized.original_timestamp,
            timezone=normalized.timezone,
            normalized_timestamp=normalized.normalized_timestamp,
            confidence=normalized.confidence,
            uncertainty_ms=uncertainty_ms(normalized),
            description=description,
            source=source,
            source_id=source_id,
            provenance=provenance,
            metadata=metadata or {},
            supporting_artifacts=supporting_artifacts or [],
        )
