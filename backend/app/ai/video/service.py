"""Application service for AI video forensic analysis."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from pathlib import PurePath
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.ai.video.bootstrap import build_video_analysis_stack
from backend.app.ai.video.config import VideoAISettings
from backend.app.ai.video.engine import ENGINE_VERSION, VideoAnalysisEngine
from backend.app.ai.video.exceptions import VideoAnalysisError
from backend.app.ai.video.models.base import VideoAIFindingItem, VideoAnalysisRunStatus
from backend.app.ai.video.models.context import VideoAnalysisContext
from backend.app.ai.video.preprocessing.frames import parse_frame_index
from backend.app.ai.video.repository import VideoAnalysisRepository
from backend.app.ai.video.schemas import (
    TemporalEvidenceResponse,
    VideoAIFindingListResponse,
    VideoAIFindingResponse,
    VideoAnalysisDetailResponse,
    VideoAnalysisRunListResponse,
    VideoAnalysisRunResponse,
    VideoFindingRegionResponse,
    VideoFrameResponse,
    VideoTimelineEntryResponse,
)
from backend.app.api.schemas.processing import ProcessingJobResponse
from backend.app.application.processors.base import ProcessorContext
from backend.app.application.processors.inspection import FileInspectionProcessor
from backend.app.application.services.artifact_service import ArtifactService
from backend.app.application.services.hashing import HashService
from backend.app.application.services.storage import StorageService
from backend.app.core.config import Settings
from backend.app.core.exceptions import (
    ConflictError,
    ProcessingError,
    ResourceNotFoundError,
)
from backend.app.domain.evidence import EvidenceStatus
from backend.app.domain.processing import (
    ArtifactType,
    EvidenceClassification,
    ProcessingJobStatus,
    ProcessingJobType,
)
from backend.app.infrastructure.database.repositories.extraction import (
    ExtractionRepository,
)
from backend.app.infrastructure.database.repositories.processing import (
    ArtifactRepository,
    ProcessingJobRepository,
)
from backend.app.models.evidence import Evidence
from backend.app.models.processing import Artifact, ProcessingJob
from backend.app.models.video_ai import (
    VideoAIFinding,
    VideoAIFindingRegion,
    VideoAnalysisRun,
)

logger = logging.getLogger(__name__)


class VideoAnalysisService:
    """Queue and execute pluggable AI video forensic detectors."""

    def __init__(
        self,
        session: AsyncSession,
        storage: StorageService,
        hash_service: HashService,
        settings: Settings,
        engine: VideoAnalysisEngine | None = None,
        video_settings: VideoAISettings | None = None,
    ) -> None:
        self.session = session
        self.storage = storage
        self.hash_service = hash_service
        self.settings = settings
        self.video_settings = video_settings or VideoAISettings()
        if engine is None:
            _, _, engine = build_video_analysis_stack(self.video_settings)
        self.engine = engine
        self.job_repository = ProcessingJobRepository(session)
        self.repository = VideoAnalysisRepository(session)
        self.extraction_repository = ExtractionRepository(session)
        self.artifact_repository = ArtifactRepository(session)
        self.artifact_service = ArtifactService(
            session,
            storage,
            hash_service,
            settings,
        )

    async def create_job(self, evidence_id: UUID) -> ProcessingJobResponse:
        evidence = await self.session.get(Evidence, evidence_id)
        if evidence is None:
            raise ResourceNotFoundError("The requested evidence was not found.")
        if evidence.status not in {
            EvidenceStatus.READY_FOR_ANALYSIS,
            EvidenceStatus.ANALYZED,
        }:
            raise ProcessingError(
                "EVIDENCE_NOT_READY",
                "Process and extract the evidence before AI video analysis.",
            )
        classification = await self._classification(evidence)
        if classification != EvidenceClassification.VIDEO:
            raise ProcessingError(
                "UNSUPPORTED_EVIDENCE",
                "AI video analysis requires video evidence.",
            )
        await FileInspectionProcessor(
            self.storage,
            self.hash_service,
        ).process(
            ProcessorContext(
                evidence=evidence,
                extension=PurePath(evidence.original_filename)
                .suffix.lower()
                .lstrip("."),
            )
        )
        active = await self.job_repository.get_active(
            evidence_id,
            ProcessingJobType.VIDEO_AI_ANALYSIS,
        )
        if active is not None:
            raise ConflictError("An active AI video analysis job already exists.")
        job = ProcessingJob(
            id=uuid4(),
            evidence_id=evidence_id,
            job_type=ProcessingJobType.VIDEO_AI_ANALYSIS,
            status=ProcessingJobStatus.QUEUED,
            priority=0,
            attempt=0,
            max_attempts=1,
            metadata_json={
                "runner": "local",
                "source_sha256": evidence.sha256_hash,
                "engine_version": ENGINE_VERSION,
            },
        )
        try:
            await self.job_repository.add(job)
            await self.session.commit()
            await self.session.refresh(job)
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError(
                "An active AI video analysis job already exists.",
            ) from exc
        return self._job_response(job)

    async def run(self, job_id: UUID) -> None:
        job = await self.job_repository.get(job_id)
        if (
            job is None
            or job.status != ProcessingJobStatus.QUEUED
            or job.job_type != ProcessingJobType.VIDEO_AI_ANALYSIS
        ):
            return
        evidence = await self.session.get(Evidence, job.evidence_id)
        if evidence is None:
            await self._fail_job(
                job_id,
                None,
                "EVIDENCE_NOT_FOUND",
                "The evidence record is no longer available.",
            )
            return
        job.status = ProcessingJobStatus.RUNNING
        job.attempt += 1
        job.started_at = datetime.now(UTC)
        analysis_run = VideoAnalysisRun(
            id=uuid4(),
            evidence_id=evidence.id,
            processing_job_id=job.id,
            status=VideoAnalysisRunStatus.RUNNING,
            engine_version=ENGINE_VERSION,
            device=self.video_settings.default_device,
            findings_count=0,
            started_at=datetime.now(UTC),
            metadata_json={"source_sha256": evidence.sha256_hash},
            timeline_json=[],
        )
        created_artifacts: list[Artifact] = []
        try:
            await self.repository.add_run(analysis_run)
            await self.session.commit()
            context = await self._context(evidence)
            result = await self.engine.analyze(context)
            if result.status != VideoAnalysisRunStatus.SUCCEEDED:
                raise VideoAnalysisError(
                    result.error_code or "ANALYSIS_FAILED",
                    result.error_message_safe or "AI video analysis failed.",
                )
            frame_artifacts: dict[int, UUID] = {}
            prediction_artifacts: dict[str, UUID] = {}
            for payload in result.artifacts:
                artifact = await self.artifact_service.create(evidence, payload)
                created_artifacts.append(artifact)
                if payload.artifact_type == ArtifactType.AI_VIDEO_FRAME:
                    frame_number = payload.metadata.get("frame_number")
                    if isinstance(frame_number, int):
                        frame_artifacts[frame_number] = artifact.id
                elif payload.artifact_type == ArtifactType.AI_VIDEO_PREDICTION:
                    detector = str(payload.metadata.get("detector", "unknown"))
                    prediction_artifacts[detector] = artifact.id
            findings_count = 0
            for item in result.findings:
                artifact_id = prediction_artifacts.get(item.detector)
                await self._persist_finding(
                    analysis_run,
                    evidence.id,
                    item,
                    artifact_id=artifact_id,
                )
                findings_count += 1
            analysis_run.status = VideoAnalysisRunStatus.SUCCEEDED
            analysis_run.findings_count = findings_count
            analysis_run.latency_ms = result.latency_ms
            analysis_run.device = result.device
            analysis_run.completed_at = datetime.now(UTC)
            analysis_run.timeline_json = [dict(entry) for entry in result.timeline]
            analysis_run.metadata_json = {
                **analysis_run.metadata_json,
                **result.metadata,
                "frame_artifacts": {
                    str(key): str(value) for key, value in frame_artifacts.items()
                },
            }
            evidence.metadata_json = {
                **evidence.metadata_json,
                "ai_video_analysis": {
                    "status": result.status.value,
                    "engine_version": ENGINE_VERSION,
                    "findings_count": findings_count,
                    "latency_ms": result.latency_ms,
                    "device": result.device,
                },
            }
            job.status = ProcessingJobStatus.SUCCEEDED
            job.completed_at = datetime.now(UTC)
            job.metadata_json = {
                **job.metadata_json,
                "video_analysis_run_id": str(analysis_run.id),
                "findings_count": findings_count,
                "latency_ms": result.latency_ms,
            }
            await self.session.commit()
        except Exception as exc:
            await self.session.rollback()
            for artifact in created_artifacts:
                await self.artifact_service.cleanup(artifact)
            if isinstance(exc, VideoAnalysisError):
                error_code = exc.code
                safe_message = exc.message
            elif isinstance(exc, ProcessingError):
                error_code = exc.code
                safe_message = exc.message
            else:
                error_code = "VIDEO_ANALYSIS_FAILED"
                safe_message = "The AI video analysis pipeline failed."
            await self._fail_job(job_id, analysis_run.id, error_code, safe_message)
            logger.exception(
                "AI video analysis job failed",
                extra={"job_id": str(job_id), "evidence_id": str(evidence.id)},
            )

    async def list_runs(
        self,
        evidence_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> VideoAnalysisRunListResponse:
        if await self.session.get(Evidence, evidence_id) is None:
            raise ResourceNotFoundError("The requested evidence was not found.")
        runs, total = await self.repository.list_runs_for_evidence(
            evidence_id,
            limit=limit,
            offset=offset,
        )
        return VideoAnalysisRunListResponse(
            items=[self._run_response(run) for run in runs],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_run(self, analysis_id: UUID) -> VideoAnalysisRunResponse:
        run = await self.repository.get_run(analysis_id)
        if run is None:
            raise ResourceNotFoundError(
                "The requested video analysis run was not found.",
            )
        return self._run_response(run)

    async def get_run_detail(self, analysis_id: UUID) -> VideoAnalysisDetailResponse:
        run = await self.repository.get_run(analysis_id)
        if run is None:
            raise ResourceNotFoundError(
                "The requested video analysis run was not found.",
            )
        frames = await self._frames_for_run(run)
        artifacts, _ = await self.repository.list_visualization_artifacts(
            run.evidence_id,
            limit=100,
            offset=0,
        )
        base = self._run_response(run)
        return VideoAnalysisDetailResponse(
            **base.model_dump(),
            timeline=[
                VideoTimelineEntryResponse(**entry)
                for entry in run.timeline_json
                if isinstance(entry, dict)
            ],
            frames=frames,
            artifacts=[
                {
                    "id": str(item.id),
                    "artifact_type": item.artifact_type.value,
                    "sha256_hash": item.sha256_hash,
                    "metadata": item.metadata_json,
                }
                for item in artifacts
            ],
        )

    async def list_findings(
        self,
        evidence_id: UUID,
        *,
        limit: int,
        offset: int,
        detector: str | None = None,
    ) -> VideoAIFindingListResponse:
        if await self.session.get(Evidence, evidence_id) is None:
            raise ResourceNotFoundError("The requested evidence was not found.")
        findings, total = await self.repository.list_findings_for_evidence(
            evidence_id,
            limit=limit,
            offset=offset,
            detector=detector,
        )
        return VideoAIFindingListResponse(
            items=[self._finding_response(item) for item in findings],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def list_frames(self, analysis_id: UUID) -> list[VideoFrameResponse]:
        run = await self.repository.get_run(analysis_id)
        if run is None:
            raise ResourceNotFoundError(
                "The requested video analysis run was not found.",
            )
        return await self._frames_for_run(run)

    async def list_timeline(
        self,
        analysis_id: UUID,
    ) -> list[VideoTimelineEntryResponse]:
        run = await self.repository.get_run(analysis_id)
        if run is None:
            raise ResourceNotFoundError(
                "The requested video analysis run was not found.",
            )
        return [
            VideoTimelineEntryResponse(**entry)
            for entry in run.timeline_json
            if isinstance(entry, dict)
        ]

    async def _frames_for_run(self, run: VideoAnalysisRun) -> list[VideoFrameResponse]:
        frame_map = run.metadata_json.get("frame_artifacts", {})
        if not isinstance(frame_map, dict):
            frame_map = {}
        video_meta = run.metadata_json.get("video", {})
        frames_meta = run.metadata_json.get("frames_sampled")
        timeline_artifacts, _ = await self.artifact_repository.list_for_evidence(
            run.evidence_id,
            artifact_types=(ArtifactType.AI_VIDEO_TIMELINE,),
            limit=1,
            offset=0,
        )
        frame_entries: list[dict[str, object]] = []
        if timeline_artifacts:
            try:
                artifact = timeline_artifacts[0]
                async with self.storage.open(artifact.storage_key) as stream:
                    raw = await asyncio.to_thread(stream.read)
                    payload = parse_frame_index(raw)
                raw_frames = payload.get("frames")
                if isinstance(raw_frames, list):
                    frame_entries = [
                        entry for entry in raw_frames if isinstance(entry, dict)
                    ]
            except OSError:
                frame_entries = []
        if not frame_entries:
            requested = run.metadata_json.get("requested_frame_timestamps")
            if isinstance(requested, list):
                frame_entries = [
                    entry for entry in requested if isinstance(entry, dict)
                ]
        responses: list[VideoFrameResponse] = []
        for index, entry in enumerate(frame_entries):
            frame_number = int(str(entry.get("frame_number", index + 1)))
            timestamp_ms = int(str(entry.get("timestamp_ms", 0)))
            artifact_id_raw = frame_map.get(str(frame_number))
            width_value = entry.get("width")
            height_value = entry.get("height")
            responses.append(
                VideoFrameResponse(
                    frame_index=int(str(entry.get("frame_index", index))),
                    frame_number=frame_number,
                    timestamp_ms=timestamp_ms,
                    timestamp_seconds=round(timestamp_ms / 1000.0, 3),
                    frame_id=str(entry.get("frame_id", "")),
                    artifact_id=(
                        UUID(str(artifact_id_raw)) if artifact_id_raw else None
                    ),
                    width=width_value if isinstance(width_value, int) else None,
                    height=height_value if isinstance(height_value, int) else None,
                )
            )
        if not responses and isinstance(video_meta, dict):
            responses.append(
                VideoFrameResponse(
                    frame_index=0,
                    frame_number=1,
                    timestamp_ms=0,
                    timestamp_seconds=0.0,
                    frame_id="",
                )
            )
        _ = frames_meta
        return responses

    async def _context(self, evidence: Evidence) -> VideoAnalysisContext:
        classification = await self._classification(evidence)
        extraction_records, _ = await self.extraction_repository.list_for_evidence(
            evidence.id,
            extraction_type=None,
            limit=50,
            offset=0,
        )
        extraction_metadata: dict[str, object] = {}
        for record in extraction_records:
            if record.metadata_json:
                extraction_metadata.update(record.metadata_json)
        extraction_artifacts, _ = await self.artifact_repository.list_for_evidence(
            evidence.id,
            artifact_types=(
                ArtifactType.VIDEO_FRAME_INDEX,
                ArtifactType.METADATA,
            ),
            limit=20,
            offset=0,
        )
        frame_index: dict[str, object] = {}
        for artifact in extraction_artifacts:
            if artifact.artifact_type != ArtifactType.VIDEO_FRAME_INDEX:
                continue
            try:
                async with self.storage.open(artifact.storage_key) as stream:
                    raw = await asyncio.to_thread(stream.read)
                    frame_index = parse_frame_index(raw)
            except OSError:
                frame_index = {}
        duration = extraction_metadata.get("duration")
        duration_ms = (
            int(float(str(duration)) * 1000) if duration is not None else None
        )
        fps_value = extraction_metadata.get("fps")
        fps = float(str(fps_value)) if fps_value is not None else None
        frame_count_value = extraction_metadata.get("frame_count")
        width_value = extraction_metadata.get("width")
        height_value = extraction_metadata.get("height")
        codec_value = extraction_metadata.get("codec")
        container_value = extraction_metadata.get("container")
        return VideoAnalysisContext(
            evidence_id=evidence.id,
            case_id=evidence.case_id,
            original_filename=evidence.original_filename,
            mime_type=evidence.mime_type,
            storage_key=evidence.storage_key,
            classification=classification,
            source_sha256=evidence.sha256_hash,
            storage=self.storage,
            settings=self.settings,
            video_settings=self.video_settings,
            duration_ms=duration_ms,
            fps=fps,
            frame_count=(
                int(str(frame_count_value))
                if frame_count_value is not None
                else None
            ),
            width=int(str(width_value)) if width_value is not None else None,
            height=int(str(height_value)) if height_value is not None else None,
            codec=str(codec_value) if codec_value is not None else None,
            container=str(container_value) if container_value is not None else None,
            frame_index_artifact=frame_index,
            extraction_metadata={
                key: value
                for key, value in extraction_metadata.items()
                if isinstance(key, str)
            },
            extraction_artifacts=tuple(
                {
                    "artifact_type": item.artifact_type.value,
                    "metadata": item.metadata_json,
                }
                for item in extraction_artifacts
            ),
        )

    async def _classification(self, evidence: Evidence) -> EvidenceClassification:
        raw = evidence.metadata_json.get("classification")
        if isinstance(raw, str):
            try:
                return EvidenceClassification(raw)
            except ValueError:
                pass
        artifacts, _ = await self.artifact_repository.list_for_evidence(
            evidence.id,
            artifact_types=(ArtifactType.CLASSIFICATION,),
            limit=1,
            offset=0,
        )
        if artifacts:
            meta = artifacts[0].metadata_json
            raw_value = meta.get("classification")
            if isinstance(raw_value, str):
                try:
                    return EvidenceClassification(raw_value)
                except ValueError:
                    pass
        return EvidenceClassification.UNKNOWN

    async def _persist_finding(
        self,
        analysis_run: VideoAnalysisRun,
        evidence_id: UUID,
        item: VideoAIFindingItem,
        *,
        artifact_id: UUID | None,
    ) -> None:
        temporal = item.temporal
        finding = VideoAIFinding(
            id=uuid4(),
            analysis_run_id=analysis_run.id,
            evidence_id=evidence_id,
            detector=item.detector,
            category=item.category,
            severity=item.severity,
            confidence=item.confidence,
            method=item.method,
            description=item.description,
            explanation=item.explanation,
            recommendation=item.recommendation,
            limitations=item.limitations,
            model_name=item.model_name,
            model_version=item.model_version,
            model_framework=item.model_framework,
            start_frame=temporal.start_frame if temporal else None,
            end_frame=temporal.end_frame if temporal else None,
            start_timestamp_ms=temporal.start_timestamp_ms if temporal else None,
            end_timestamp_ms=temporal.end_timestamp_ms if temporal else None,
            artifact_id=artifact_id,
            metadata_json=item.metadata,
        )
        await self.repository.add_finding(finding)
        for region in item.regions:
            await self.repository.add_region(
                VideoAIFindingRegion(
                    id=uuid4(),
                    finding_id=finding.id,
                    x=region.x,
                    y=region.y,
                    width=region.width,
                    height=region.height,
                    frame_number=region.frame_number,
                    timestamp_ms=(
                        temporal.start_timestamp_ms if temporal else None
                    ),
                    polygon_json=(
                        [list(point) for point in region.polygon]
                        if region.polygon
                        else None
                    ),
                    normalized_x=region.normalized.x if region.normalized else None,
                    normalized_y=region.normalized.y if region.normalized else None,
                    normalized_width=(
                        region.normalized.width if region.normalized else None
                    ),
                    normalized_height=(
                        region.normalized.height if region.normalized else None
                    ),
                )
            )

    async def _fail_job(
        self,
        job_id: UUID,
        analysis_run_id: UUID | None,
        error_code: str,
        message: str,
    ) -> None:
        job = await self.job_repository.get(job_id)
        if job is not None:
            job.status = ProcessingJobStatus.FAILED
            job.error_code = error_code
            job.error_message_safe = message
            job.completed_at = datetime.now(UTC)
        if analysis_run_id is not None:
            run = await self.repository.get_run(analysis_run_id)
            if run is not None:
                run.status = VideoAnalysisRunStatus.FAILED
                run.error_code = error_code
                run.error_message = message
                run.completed_at = datetime.now(UTC)
        await self.session.commit()

    @staticmethod
    def _job_response(job: ProcessingJob) -> ProcessingJobResponse:
        return ProcessingJobResponse(
            id=job.id,
            evidence_id=job.evidence_id,
            job_type=job.job_type,
            status=job.status,
            priority=job.priority,
            attempt=job.attempt,
            max_attempts=job.max_attempts,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            updated_at=job.updated_at,
            error_code=job.error_code,
            error_message=job.error_message_safe,
            metadata=job.metadata_json,
        )

    @staticmethod
    def _run_response(run: VideoAnalysisRun) -> VideoAnalysisRunResponse:
        video_meta = run.metadata_json.get("video")
        return VideoAnalysisRunResponse(
            id=run.id,
            evidence_id=run.evidence_id,
            status=run.status,
            engine_version=run.engine_version,
            device=run.device,
            latency_ms=run.latency_ms,
            findings_count=run.findings_count,
            created_at=run.created_at,
            started_at=run.started_at,
            completed_at=run.completed_at,
            error_code=run.error_code,
            error_message=run.error_message,
            metadata=run.metadata_json,
            video=video_meta if isinstance(video_meta, dict) else None,
        )

    @staticmethod
    def _region_responses(
        regions: list[VideoAIFindingRegion],
    ) -> list[VideoFindingRegionResponse]:
        responses: list[VideoFindingRegionResponse] = []
        for region in regions:
            responses.append(
                VideoFindingRegionResponse(
                    x=region.x,
                    y=region.y,
                    width=region.width,
                    height=region.height,
                    frame_number=region.frame_number,
                    timestamp_ms=region.timestamp_ms,
                    polygon=(
                        [
                            (float(point[0]), float(point[1]))
                            for point in region.polygon_json
                        ]
                        if region.polygon_json
                        else None
                    ),
                    normalized_location=(
                        {
                            "x": region.normalized_x,
                            "y": region.normalized_y,
                            "width": region.normalized_width,
                            "height": region.normalized_height,
                        }
                        if region.normalized_x is not None
                        and region.normalized_y is not None
                        and region.normalized_width is not None
                        and region.normalized_height is not None
                        else None
                    ),
                )
            )
        return responses

    @staticmethod
    def _finding_response(finding: VideoAIFinding) -> VideoAIFindingResponse:
        temporal = None
        if (
            finding.start_frame is not None
            or finding.start_timestamp_ms is not None
        ):
            temporal = TemporalEvidenceResponse(
                start_frame=finding.start_frame,
                end_frame=finding.end_frame,
                start_timestamp_ms=finding.start_timestamp_ms,
                end_timestamp_ms=finding.end_timestamp_ms,
            )
        return VideoAIFindingResponse(
            id=finding.id,
            analysis_run_id=finding.analysis_run_id,
            detector=finding.detector,
            category=finding.category,
            severity=finding.severity,
            confidence=finding.confidence,
            method=finding.method,
            description=finding.description,
            explanation=finding.explanation,
            recommendation=finding.recommendation,
            model_name=finding.model_name,
            model_version=finding.model_version,
            model_framework=finding.model_framework,
            temporal=temporal,
            artifact_id=finding.artifact_id,
            regions=VideoAnalysisService._region_responses(finding.regions),
            metadata=finding.metadata_json,
            limitations=finding.limitations,
            created_at=finding.created_at,
        )
