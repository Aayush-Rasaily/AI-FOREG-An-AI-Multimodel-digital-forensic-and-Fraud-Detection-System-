"""Collect and aggregate normalized findings for one evidence item."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.domain.processing import EvidenceClassification
from backend.app.fusion.models import (
    Modality,
    ModalityAvailability,
    ModalityStatus,
    NormalizedFinding,
)
from backend.app.fusion.normalization import (
    deduplicate_findings,
    normalize_ai_finding,
    normalize_comparison_difference,
    normalize_forensic_finding,
    normalize_signature_verdict,
)
from backend.app.models.audio_ai import AudioAIFinding
from backend.app.models.comparison import Difference
from backend.app.models.document_ai import DocumentAIFinding
from backend.app.models.evidence import Evidence
from backend.app.models.forensics import Finding
from backend.app.models.image_ai import ImageAIFinding
from backend.app.models.signature_ai import SignatureVerificationRun
from backend.app.models.video_ai import VideoAIFinding


def modality_for_classification(
    classification: EvidenceClassification,
) -> Modality | None:
    mapping = {
        EvidenceClassification.IMAGE: Modality.IMAGE_AI,
        EvidenceClassification.DOCUMENT: Modality.DOCUMENT_AI,
        EvidenceClassification.VIDEO: Modality.VIDEO_AI,
        EvidenceClassification.AUDIO: Modality.AUDIO_AI,
    }
    return mapping.get(classification)


async def collect_normalized_findings(
    session: AsyncSession,
    evidence: Evidence,
    classification: EvidenceClassification,
) -> tuple[tuple[NormalizedFinding, ...], tuple[ModalityStatus, ...]]:
    """Gather normalized findings from all available modality stores."""

    findings: list[NormalizedFinding] = []
    statuses: list[ModalityStatus] = []

    forensic_rows = await session.scalars(
        select(Finding)
        .where(Finding.evidence_id == evidence.id)
        .order_by(Finding.created_at, Finding.id)
    )
    forensic_list = list(forensic_rows)
    for row in forensic_list:
        findings.append(
            normalize_forensic_finding(
                evidence_id=evidence.id,
                finding_id=row.id,
                detector=row.detector,
                category=row.category.value,
                severity=row.severity,
                confidence=row.confidence,
                description=row.description,
                explanation=row.explanation,
                metadata=row.metadata_json,
            )
        )
    statuses.append(
        ModalityStatus(
            modality=Modality.FORENSICS,
            availability=(
                ModalityAvailability.AVAILABLE
                if forensic_list
                else ModalityAvailability.INSUFFICIENT_EVIDENCE
            ),
            findings_count=len(forensic_list),
            reason=None if forensic_list else "No forensic findings recorded.",
        )
    )

    image_rows = list(
        await session.scalars(
            select(ImageAIFinding)
            .where(ImageAIFinding.evidence_id == evidence.id)
            .order_by(ImageAIFinding.created_at, ImageAIFinding.id)
        )
    )
    for image_row in image_rows:
        temporal_raw = image_row.metadata_json.get("temporal")
        temporal = temporal_raw if isinstance(temporal_raw, dict) else None
        findings.append(
            normalize_ai_finding(
                modality=Modality.IMAGE_AI,
                evidence_id=evidence.id,
                finding_id=image_row.id,
                detector=image_row.detector,
                category=image_row.category.value,
                severity=image_row.severity,
                confidence=image_row.confidence,
                description=image_row.description,
                explanation=image_row.explanation,
                model_name=image_row.model_name,
                model_version=image_row.model_version,
                temporal=temporal,
                metadata=image_row.metadata_json,
            )
        )
    _append_modality_status(
        statuses,
        Modality.IMAGE_AI,
        image_rows,
        classification == EvidenceClassification.IMAGE,
    )

    document_rows = list(
        await session.scalars(
            select(DocumentAIFinding)
            .where(DocumentAIFinding.evidence_id == evidence.id)
            .order_by(DocumentAIFinding.created_at, DocumentAIFinding.id)
        )
    )
    for document_row in document_rows:
        findings.append(
            normalize_ai_finding(
                modality=Modality.DOCUMENT_AI,
                evidence_id=evidence.id,
                finding_id=document_row.id,
                detector=document_row.detector,
                category=document_row.category.value,
                severity=document_row.severity,
                confidence=document_row.confidence,
                description=document_row.description,
                explanation=document_row.explanation,
                model_name=document_row.model_name,
                model_version=document_row.model_version,
                metadata=document_row.metadata_json,
            )
        )
    _append_modality_status(
        statuses,
        Modality.DOCUMENT_AI,
        document_rows,
        classification == EvidenceClassification.DOCUMENT,
    )

    video_rows = list(
        await session.scalars(
            select(VideoAIFinding)
            .where(VideoAIFinding.evidence_id == evidence.id)
            .order_by(VideoAIFinding.created_at, VideoAIFinding.id)
        )
    )
    for video_row in video_rows:
        temporal = None
        if (
            video_row.start_timestamp_ms is not None
            or video_row.end_timestamp_ms is not None
        ):
            temporal = {
                "start_timestamp_ms": video_row.start_timestamp_ms,
                "end_timestamp_ms": video_row.end_timestamp_ms,
            }
        findings.append(
            normalize_ai_finding(
                modality=Modality.VIDEO_AI,
                evidence_id=evidence.id,
                finding_id=video_row.id,
                detector=video_row.detector,
                category=video_row.category.value,
                severity=video_row.severity,
                confidence=video_row.confidence,
                description=video_row.description,
                explanation=video_row.explanation,
                model_name=video_row.model_name,
                model_version=video_row.model_version,
                temporal=temporal,
                metadata=video_row.metadata_json,
            )
        )
    _append_modality_status(
        statuses,
        Modality.VIDEO_AI,
        video_rows,
        classification == EvidenceClassification.VIDEO,
    )

    audio_rows = list(
        await session.scalars(
            select(AudioAIFinding)
            .where(AudioAIFinding.evidence_id == evidence.id)
            .order_by(AudioAIFinding.created_at, AudioAIFinding.id)
        )
    )
    for audio_row in audio_rows:
        temporal = None
        if audio_row.start_time_ms is not None or audio_row.end_time_ms is not None:
            temporal = {
                "start_time_ms": audio_row.start_time_ms,
                "end_time_ms": audio_row.end_time_ms,
                "duration_ms": audio_row.duration_ms,
            }
        findings.append(
            normalize_ai_finding(
                modality=Modality.AUDIO_AI,
                evidence_id=evidence.id,
                finding_id=audio_row.id,
                detector=audio_row.detector,
                category=audio_row.category.value,
                severity=audio_row.severity,
                confidence=audio_row.confidence,
                description=audio_row.description,
                explanation=audio_row.explanation,
                model_name=audio_row.model_name,
                model_version=audio_row.model_version,
                temporal=temporal,
                metadata=audio_row.metadata_json,
            )
        )
    _append_modality_status(
        statuses,
        Modality.AUDIO_AI,
        audio_rows,
        classification == EvidenceClassification.AUDIO,
    )

    signature_rows = list(
        await session.scalars(
            select(SignatureVerificationRun)
            .where(SignatureVerificationRun.questioned_evidence_id == evidence.id)
            .order_by(SignatureVerificationRun.created_at, SignatureVerificationRun.id)
        )
    )
    for signature_row in signature_rows:
        findings.append(
            normalize_signature_verdict(
                evidence_id=evidence.id,
                run_id=signature_row.id,
                verdict=signature_row.verdict,
                similarity=signature_row.similarity,
                model_name=signature_row.model_name,
                model_version=signature_row.model_version,
                metadata=signature_row.metadata_json,
            )
        )
    statuses.append(
        ModalityStatus(
            modality=Modality.SIGNATURE_AI,
            availability=(
                ModalityAvailability.AVAILABLE
                if signature_rows
                else ModalityAvailability.NOT_APPLICABLE
            ),
            findings_count=len(signature_rows),
            reason=None if signature_rows else "No signature verification runs.",
        )
    )

    comparison_rows = list(
        await session.scalars(
            select(Difference)
            .where(Difference.evidence_id == evidence.id)
            .order_by(Difference.created_at, Difference.id)
        )
    )
    for difference_row in comparison_rows:
        findings.append(
            normalize_comparison_difference(
                evidence_id=evidence.id,
                difference_id=difference_row.id,
                matcher=difference_row.matcher,
                difference_type=difference_row.difference_type.value,
                severity=difference_row.severity,
                confidence=difference_row.confidence,
                description=difference_row.description,
                explanation=difference_row.explanation,
                metadata=difference_row.metadata_json,
            )
        )
    statuses.append(
        ModalityStatus(
            modality=Modality.COMPARISON,
            availability=(
                ModalityAvailability.AVAILABLE
                if comparison_rows
                else ModalityAvailability.INSUFFICIENT_EVIDENCE
            ),
            findings_count=len(comparison_rows),
            reason=None if comparison_rows else "No comparison differences recorded.",
        )
    )

    return deduplicate_findings(tuple(findings)), tuple(statuses)


def _append_modality_status(
    statuses: list[ModalityStatus],
    modality: Modality,
    rows: Sequence[object],
    applicable: bool,
) -> None:
    if not applicable:
        statuses.append(
            ModalityStatus(
                modality=modality,
                availability=ModalityAvailability.NOT_APPLICABLE,
                findings_count=len(rows),
                reason="Modality not applicable for evidence classification.",
            )
        )
        return
    if rows:
        statuses.append(
            ModalityStatus(
                modality=modality,
                availability=ModalityAvailability.AVAILABLE,
                findings_count=len(rows),
            )
        )
        return
    statuses.append(
        ModalityStatus(
            modality=modality,
            availability=ModalityAvailability.INSUFFICIENT_EVIDENCE,
            findings_count=0,
            reason="No findings recorded for this modality.",
        )
    )
