"""Application service for AI audio forensic analysis."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from pathlib import PurePath
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.ai.audio.bootstrap import build_audio_analysis_stack
from backend.app.ai.audio.config import AudioAISettings
from backend.app.ai.audio.engine import ENGINE_VERSION, AudioAnalysisEngine
from backend.app.ai.audio.exceptions import AudioAnalysisError
from backend.app.ai.audio.models import (
    AudioAIFindingItem,
    AudioAnalysisContext,
    AudioAnalysisRunStatus,
)
from backend.app.ai.audio.preprocessing.audio import load_bounded_audio
from backend.app.ai.audio.repository import AudioAnalysisRepository
from backend.app.ai.audio.schemas import (
    AudioAIFindingListResponse,
    AudioAIFindingResponse,
    AudioAnalysisDetailResponse,
    AudioAnalysisRunListResponse,
    AudioAnalysisRunResponse,
    AudioFeatureSummaryResponse,
    AudioFindingRegionResponse,
    AudioSegmentResponse,
    AudioTimelineEntryResponse,
    TemporalEvidenceResponse,
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
from backend.app.models.audio_ai import (
    AudioAIFinding,
    AudioAIFindingRegion,
    AudioAnalysisRun,
)
from backend.app.models.evidence import Evidence
from backend.app.models.processing import Artifact, ProcessingJob

logger = logging.getLogger(__name__)


class AudioAnalysisService:
    """Queue and execute pluggable AI audio forensic detectors."""

    def __init__(
        self,
        session: AsyncSession,
        storage: StorageService,
        hash_service: HashService,
        settings: Settings,
        engine: AudioAnalysisEngine | None = None,
        audio_settings: AudioAISettings | None = None,
    ) -> None:
        self.session = session
        self.storage = storage
        self.hash_service = hash_service
        self.settings = settings
        self.audio_settings = audio_settings or AudioAISettings()
        if engine is None:
            _, _, engine = build_audio_analysis_stack(self.audio_settings)
        self.engine = engine
        self.job_repository = ProcessingJobRepository(session)
        self.repository = AudioAnalysisRepository(session)
        self.extraction_repository = ExtractionRepository(session)
        self.artifact_repository = ArtifactRepository(session)
        self.artifact_service = ArtifactService(
            session,
            storage,
            hash_service,
            settings,
        )

    async def create_job(
        self,
        evidence_id: UUID,
        *,
        reference_evidence_id: UUID | None = None,
    ) -> ProcessingJobResponse:
        evidence = await self.session.get(Evidence, evidence_id)
        if evidence is None:
            raise ResourceNotFoundError("The requested evidence was not found.")
        if evidence.status not in {
            EvidenceStatus.READY_FOR_ANALYSIS,
            EvidenceStatus.ANALYZED,
        }:
            raise ProcessingError(
                "EVIDENCE_NOT_READY",
                "Process and extract the evidence before AI audio analysis.",
            )
        classification = await self._classification(evidence)
        if classification != EvidenceClassification.AUDIO:
            raise ProcessingError(
                "UNSUPPORTED_EVIDENCE",
                "AI audio analysis requires audio evidence.",
            )
        if reference_evidence_id is not None:
            reference = await self.session.get(Evidence, reference_evidence_id)
            if reference is None:
                raise ResourceNotFoundError(
                    "The requested reference evidence was not found.",
                )
            ref_class = await self._classification(reference)
            if ref_class != EvidenceClassification.AUDIO:
                raise ProcessingError(
                    "UNSUPPORTED_REFERENCE",
                    "Reference evidence must be audio.",
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
            ProcessingJobType.AUDIO_AI_ANALYSIS,
        )
        if active is not None:
            raise ConflictError("An active AI audio analysis job already exists.")
        job = ProcessingJob(
            id=uuid4(),
            evidence_id=evidence_id,
            job_type=ProcessingJobType.AUDIO_AI_ANALYSIS,
            status=ProcessingJobStatus.QUEUED,
            priority=0,
            attempt=0,
            max_attempts=1,
            metadata_json={
                "runner": "local",
                "source_sha256": evidence.sha256_hash,
                "engine_version": ENGINE_VERSION,
                "reference_evidence_id": (
                    str(reference_evidence_id) if reference_evidence_id else None
                ),
            },
        )
        try:
            await self.job_repository.add(job)
            await self.session.commit()
            await self.session.refresh(job)
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError(
                "An active AI audio analysis job already exists.",
            ) from exc
        return self._job_response(job)

    async def run(self, job_id: UUID) -> None:
        job = await self.job_repository.get(job_id)
        if (
            job is None
            or job.status != ProcessingJobStatus.QUEUED
            or job.job_type != ProcessingJobType.AUDIO_AI_ANALYSIS
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
        reference_id_raw = job.metadata_json.get("reference_evidence_id")
        reference_evidence_id = (
            UUID(str(reference_id_raw)) if reference_id_raw else None
        )
        job.status = ProcessingJobStatus.RUNNING
        job.attempt += 1
        job.started_at = datetime.now(UTC)
        analysis_run = AudioAnalysisRun(
            id=uuid4(),
            evidence_id=evidence.id,
            processing_job_id=job.id,
            reference_evidence_id=reference_evidence_id,
            status=AudioAnalysisRunStatus.RUNNING,
            engine_version=ENGINE_VERSION,
            device=self.audio_settings.default_device,
            findings_count=0,
            started_at=datetime.now(UTC),
            metadata_json={"source_sha256": evidence.sha256_hash},
            timeline_json=[],
            segments_json=[],
        )
        created_artifacts: list[Artifact] = []
        try:
            await self.repository.add_run(analysis_run)
            await self.session.commit()
            context = await self._context(
                evidence,
                reference_evidence_id=reference_evidence_id,
            )
            result = await self.engine.analyze(context)
            if result.status != AudioAnalysisRunStatus.SUCCEEDED:
                raise AudioAnalysisError(
                    result.error_code or "ANALYSIS_FAILED",
                    result.error_message_safe or "AI audio analysis failed.",
                )
            prediction_artifacts: dict[str, UUID] = {}
            for payload in result.artifacts:
                artifact = await self.artifact_service.create(evidence, payload)
                created_artifacts.append(artifact)
                if payload.artifact_type == ArtifactType.AI_AUDIO_PREDICTION:
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
            analysis_run.status = AudioAnalysisRunStatus.SUCCEEDED
            analysis_run.findings_count = findings_count
            analysis_run.latency_ms = result.latency_ms
            analysis_run.device = result.device
            analysis_run.completed_at = datetime.now(UTC)
            analysis_run.timeline_json = [dict(entry) for entry in result.timeline]
            analysis_run.segments_json = [dict(entry) for entry in result.segments]
            analysis_run.metadata_json = {
                **analysis_run.metadata_json,
                **result.metadata,
            }
            if result.feature_summary is not None:
                analysis_run.metadata_json["feature_summary"] = (
                    result.feature_summary.to_dict()
                )
            evidence.metadata_json = {
                **evidence.metadata_json,
                "ai_audio_analysis": {
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
                "audio_analysis_run_id": str(analysis_run.id),
                "findings_count": findings_count,
                "latency_ms": result.latency_ms,
            }
            await self.session.commit()
        except Exception as exc:
            await self.session.rollback()
            for artifact in created_artifacts:
                await self.artifact_service.cleanup(artifact)
            if isinstance(exc, AudioAnalysisError):
                error_code = exc.code
                safe_message = exc.message
            elif isinstance(exc, ProcessingError):
                error_code = exc.code
                safe_message = exc.message
            else:
                error_code = "AUDIO_ANALYSIS_FAILED"
                safe_message = "The AI audio analysis pipeline failed."
            await self._fail_job(job_id, analysis_run.id, error_code, safe_message)
            logger.exception(
                "AI audio analysis job failed",
                extra={"job_id": str(job_id), "evidence_id": str(evidence.id)},
            )

    async def list_runs(
        self,
        evidence_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> AudioAnalysisRunListResponse:
        if await self.session.get(Evidence, evidence_id) is None:
            raise ResourceNotFoundError("The requested evidence was not found.")
        runs, total = await self.repository.list_runs_for_evidence(
            evidence_id,
            limit=limit,
            offset=offset,
        )
        return AudioAnalysisRunListResponse(
            items=[self._run_response(run) for run in runs],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_run(self, analysis_id: UUID) -> AudioAnalysisRunResponse:
        run = await self.repository.get_run(analysis_id)
        if run is None:
            raise ResourceNotFoundError(
                "The requested audio analysis run was not found.",
            )
        return self._run_response(run)

    async def get_run_detail(self, analysis_id: UUID) -> AudioAnalysisDetailResponse:
        run = await self.repository.get_run(analysis_id)
        if run is None:
            raise ResourceNotFoundError(
                "The requested audio analysis run was not found.",
            )
        artifacts, _ = await self.repository.list_audio_artifacts(
            run.evidence_id,
            limit=100,
            offset=0,
        )
        base = self._run_response(run)
        feature_raw = run.metadata_json.get("feature_summary")
        features = None
        if isinstance(feature_raw, dict):
            features = AudioFeatureSummaryResponse(
                sample_rate=int(feature_raw.get("sample_rate", 0)),
                duration_seconds=float(feature_raw.get("duration_seconds", 0.0)),
                channels=int(feature_raw.get("channels", 1)),
                rms_energy=float(feature_raw.get("rms_energy", 0.0)),
                zero_crossing_rate=float(feature_raw.get("zero_crossing_rate", 0.0)),
                spectral_centroid_hz=float(
                    feature_raw.get("spectral_centroid_hz", 0.0)
                ),
                mfcc_mean=list(feature_raw.get("mfcc_mean", [])),
                window_count=int(feature_raw.get("window_count", 0)),
            )
        return AudioAnalysisDetailResponse(
            **base.model_dump(),
            timeline=[
                AudioTimelineEntryResponse(**entry)
                for entry in run.timeline_json
                if isinstance(entry, dict)
            ],
            segments=[
                AudioSegmentResponse(**entry)
                for entry in run.segments_json
                if isinstance(entry, dict)
            ],
            features=features,
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
    ) -> AudioAIFindingListResponse:
        if await self.session.get(Evidence, evidence_id) is None:
            raise ResourceNotFoundError("The requested evidence was not found.")
        findings, total = await self.repository.list_findings_for_evidence(
            evidence_id,
            limit=limit,
            offset=offset,
            detector=detector,
        )
        return AudioAIFindingListResponse(
            items=[self._finding_response(item) for item in findings],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def list_timeline(
        self,
        analysis_id: UUID,
    ) -> list[AudioTimelineEntryResponse]:
        run = await self.repository.get_run(analysis_id)
        if run is None:
            raise ResourceNotFoundError(
                "The requested audio analysis run was not found.",
            )
        return [
            AudioTimelineEntryResponse(**entry)
            for entry in run.timeline_json
            if isinstance(entry, dict)
        ]

    async def list_segments(
        self,
        analysis_id: UUID,
    ) -> list[AudioSegmentResponse]:
        run = await self.repository.get_run(analysis_id)
        if run is None:
            raise ResourceNotFoundError(
                "The requested audio analysis run was not found.",
            )
        return [
            AudioSegmentResponse(**entry)
            for entry in run.segments_json
            if isinstance(entry, dict)
        ]

    async def get_features(
        self,
        analysis_id: UUID,
    ) -> AudioFeatureSummaryResponse | None:
        run = await self.repository.get_run(analysis_id)
        if run is None:
            raise ResourceNotFoundError(
                "The requested audio analysis run was not found.",
            )
        feature_raw = run.metadata_json.get("feature_summary")
        if not isinstance(feature_raw, dict):
            return None
        return AudioFeatureSummaryResponse(
            sample_rate=int(feature_raw.get("sample_rate", 0)),
            duration_seconds=float(feature_raw.get("duration_seconds", 0.0)),
            channels=int(feature_raw.get("channels", 1)),
            rms_energy=float(feature_raw.get("rms_energy", 0.0)),
            zero_crossing_rate=float(feature_raw.get("zero_crossing_rate", 0.0)),
            spectral_centroid_hz=float(feature_raw.get("spectral_centroid_hz", 0.0)),
            mfcc_mean=list(feature_raw.get("mfcc_mean", [])),
            window_count=int(feature_raw.get("window_count", 0)),
        )

    async def _context(
        self,
        evidence: Evidence,
        *,
        reference_evidence_id: UUID | None = None,
    ) -> AudioAnalysisContext:
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
        duration = extraction_metadata.get("duration")
        duration_ms = (
            int(float(str(duration)) * 1000) if duration is not None else None
        )
        sample_rate_value = extraction_metadata.get("sample_rate")
        channels_value = extraction_metadata.get("channels")
        codec_value = extraction_metadata.get("codec") or extraction_metadata.get(
            "format"
        )
        reference_samples = None
        reference_sample_rate = None
        if reference_evidence_id is not None:
            reference = await self.session.get(Evidence, reference_evidence_id)
            if reference is not None:
                ref_extension = (
                    PurePath(reference.original_filename).suffix.lower().lstrip(".")
                )
                async with self.storage.open(reference.storage_key) as stream:
                    loaded = await asyncio.to_thread(
                        load_bounded_audio,
                        stream,
                        extension=ref_extension or "wav",
                        ffmpeg_command=self.audio_settings.ffmpeg_command,
                        target_sample_rate=self.audio_settings.analysis_sample_rate,
                        max_samples=self.audio_settings.max_samples,
                        max_duration_seconds=self.audio_settings.max_duration_seconds,
                    )
                if loaded is not None:
                    reference_samples = loaded.samples
                    reference_sample_rate = loaded.sample_rate
        return AudioAnalysisContext(
            evidence_id=evidence.id,
            case_id=evidence.case_id,
            original_filename=evidence.original_filename,
            mime_type=evidence.mime_type,
            storage_key=evidence.storage_key,
            classification=classification,
            source_sha256=evidence.sha256_hash,
            storage=self.storage,
            settings=self.settings,
            audio_settings=self.audio_settings,
            duration_ms=duration_ms,
            sample_rate=(
                int(str(sample_rate_value)) if sample_rate_value is not None else None
            ),
            channels=int(str(channels_value)) if channels_value is not None else None,
            codec=str(codec_value) if codec_value is not None else None,
            reference_evidence_id=reference_evidence_id,
            reference_samples=reference_samples,
            reference_sample_rate=reference_sample_rate,
            extraction_metadata={
                key: value
                for key, value in extraction_metadata.items()
                if isinstance(key, str)
            },
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
        analysis_run: AudioAnalysisRun,
        evidence_id: UUID,
        item: AudioAIFindingItem,
        *,
        artifact_id: UUID | None,
    ) -> None:
        temporal = item.temporal
        finding = AudioAIFinding(
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
            start_time_ms=temporal.start_time_ms if temporal else None,
            end_time_ms=temporal.end_time_ms if temporal else None,
            duration_ms=temporal.duration_ms if temporal else None,
            artifact_id=artifact_id,
            metadata_json=item.metadata,
        )
        await self.repository.add_finding(finding)
        if temporal is not None:
            await self.repository.add_region(
                AudioAIFindingRegion(
                    id=uuid4(),
                    finding_id=finding.id,
                    segment_id=item.metadata.get("segment_id"),
                    start_time_ms=temporal.start_time_ms,
                    end_time_ms=temporal.end_time_ms,
                    duration_ms=temporal.duration_ms,
                    metrics_json={
                        key: value
                        for key, value in item.metadata.items()
                        if key != "segment_id"
                    },
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
                run.status = AudioAnalysisRunStatus.FAILED
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
    def _run_response(run: AudioAnalysisRun) -> AudioAnalysisRunResponse:
        audio_meta = run.metadata_json.get("audio")
        return AudioAnalysisRunResponse(
            id=run.id,
            evidence_id=run.evidence_id,
            reference_evidence_id=run.reference_evidence_id,
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
            audio=audio_meta if isinstance(audio_meta, dict) else None,
        )

    @staticmethod
    def _region_responses(
        regions: list[AudioAIFindingRegion],
    ) -> list[AudioFindingRegionResponse]:
        return [
            AudioFindingRegionResponse(
                segment_id=region.segment_id,
                start_time_ms=region.start_time_ms,
                end_time_ms=region.end_time_ms,
                duration_ms=region.duration_ms,
                metrics=region.metrics_json,
            )
            for region in regions
        ]

    @staticmethod
    def _finding_response(finding: AudioAIFinding) -> AudioAIFindingResponse:
        temporal = None
        if finding.start_time_ms is not None or finding.end_time_ms is not None:
            temporal = TemporalEvidenceResponse(
                start_time_ms=finding.start_time_ms,
                end_time_ms=finding.end_time_ms,
                duration_ms=finding.duration_ms,
            )
        return AudioAIFindingResponse(
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
            regions=AudioAnalysisService._region_responses(finding.regions),
            metadata=finding.metadata_json,
            limitations=finding.limitations,
            created_at=finding.created_at,
        )
