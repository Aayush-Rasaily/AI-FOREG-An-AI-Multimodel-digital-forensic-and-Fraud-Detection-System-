"""Cross-evidence correlation reconstruction engine."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.correlation.matchers import (
    EvidenceSignals,
    extract_emails,
    extract_identifiers,
    extract_phones,
    group_by_value,
    location_key,
    metadata_scalar,
    nested_dict,
    similar_filename_pairs,
    support_entity,
)
from backend.app.correlation.models import (
    CorrelationBuildResult,
    CorrelationSupport,
    CorrelationType,
    EvidenceCorrelation,
)
from backend.app.correlation.policy import ENGINE_VERSION, POLICY_VERSION
from backend.app.correlation.provenance import (
    build_provenance,
    canonical_pair,
    correlation_key,
)
from backend.app.correlation.scoring import confidence_for, score_for
from backend.app.extraction.models import ExtractionType
from backend.app.models.audio_ai import AudioAIFinding, AudioAnalysisRun
from backend.app.models.case import Case
from backend.app.models.evidence import Evidence
from backend.app.models.extraction import ExtractionRecord
from backend.app.models.image_ai import ImageAIFinding, ImageAnalysisRun
from backend.app.models.signature_ai import SignatureVerificationRun
from backend.app.models.timeline import InvestigationTimeline, TimelineEventRecord


class CorrelationEngine:
    """Discover deterministic relationships across case evidence."""

    async def build(
        self,
        session: AsyncSession,
        case: Case,
    ) -> CorrelationBuildResult:
        """Collect signals, match, score, and deduplicate correlations."""

        evidence_rows = list(
            await session.scalars(select(Evidence).where(Evidence.case_id == case.id))
        )
        if len(evidence_rows) < 2:
            return CorrelationBuildResult(
                correlations=(),
                provenance=build_provenance(
                    case_id=case.id,
                    case_number=case.case_number,
                )
                | {
                    "engine_version": ENGINE_VERSION,
                    "policy_version": POLICY_VERSION,
                    "evidence_count": len(evidence_rows),
                },
                metadata={
                    "correlation_count": 0,
                    "evidence_count": len(evidence_rows),
                },
            )

        signals = await self._collect_signals(session, case.id, evidence_rows)
        correlations = self._match_all(case.id, signals)
        deduped = self._deduplicate(correlations)
        ordered = tuple(
            sorted(
                deduped,
                key=lambda item: (
                    -item.score,
                    item.correlation_type.value,
                    str(item.left_evidence_id),
                    str(item.right_evidence_id),
                    item.correlation_id,
                ),
            )
        )
        return CorrelationBuildResult(
            correlations=ordered,
            provenance={
                **build_provenance(case_id=case.id, case_number=case.case_number),
                "engine_version": ENGINE_VERSION,
                "policy_version": POLICY_VERSION,
                "evidence_count": len(evidence_rows),
            },
            metadata={
                "correlation_count": len(ordered),
                "evidence_count": len(evidence_rows),
            },
        )

    async def _collect_signals(
        self,
        session: AsyncSession,
        case_id: UUID,
        evidence_rows: list[Evidence],
    ) -> list[EvidenceSignals]:
        evidence_ids = [item.id for item in evidence_rows]
        by_id = {
            item.id: EvidenceSignals(
                evidence_id=item.id,
                evidence_number=item.evidence_number,
                sha256_hash=item.sha256_hash,
                original_filename=item.original_filename,
                mime_type=item.mime_type,
            )
            for item in evidence_rows
        }

        for evidence in evidence_rows:
            signal = by_id[evidence.id]
            metadata = (
                evidence.metadata_json
                if isinstance(evidence.metadata_json, dict)
                else {}
            )
            exif = nested_dict(metadata, "exif")
            camera = metadata_scalar(
                exif,
                "Model",
                "CameraModel",
                "camera_model",
                "Make",
            ) or metadata_scalar(metadata, "camera_model", "device_model")
            if camera:
                signal.camera_models.add(camera)
                signal.metadata_fields["camera_model"] = camera
            device = metadata_scalar(
                exif,
                "DeviceModel",
                "device_model",
                "Software",
            ) or metadata_scalar(metadata, "device_model")
            if device:
                signal.device_models.add(device)
                signal.metadata_fields["device_model"] = device
            loc = location_key(metadata)
            if loc:
                signal.locations.add(loc)
                signal.metadata_fields["location"] = loc
            creator = metadata_scalar(
                nested_dict(metadata, "processing"),
                "creator",
                "author",
            )
            if creator:
                signal.metadata_fields["creator"] = creator

        extraction_rows = list(
            await session.scalars(
                select(ExtractionRecord).where(
                    ExtractionRecord.evidence_id.in_(evidence_ids)
                )
            )
        )
        for record in extraction_rows:
            signal = by_id[record.evidence_id]
            signal.extraction_ids.append(str(record.id))
            content = (record.content or "").strip()
            if not content:
                continue
            if record.extraction_type in {
                ExtractionType.TEXT,
                ExtractionType.LINE,
                ExtractionType.WORD,
                ExtractionType.PAGE,
            }:
                signal.emails.update(extract_emails(content))
                signal.phones.update(extract_phones(content))
                signal.identifiers.update(extract_identifiers(content))
                signal.document_ids.update(extract_identifiers(content))
            if record.extraction_type == ExtractionType.QR_CODE:
                signal.qr_payloads.add(content)
            if record.extraction_type == ExtractionType.NUMBER:
                signal.identifiers.add(content.upper())
            if record.extraction_type == ExtractionType.LOGO_REGION:
                signal.logo_labels.add(content or f"logo:{record.id}")

        image_runs = list(
            await session.scalars(
                select(ImageAnalysisRun).where(
                    ImageAnalysisRun.evidence_id.in_(evidence_ids)
                )
            )
        )
        if image_runs:
            image_run_ids = [item.id for item in image_runs]
            image_by_id = {item.id: item for item in image_runs}
            image_findings = list(
                await session.scalars(
                    select(ImageAIFinding).where(
                        ImageAIFinding.analysis_run_id.in_(image_run_ids)
                    )
                )
            )
            for image_finding in image_findings:
                category = getattr(
                    image_finding.category,
                    "value",
                    str(image_finding.category),
                )
                if category.upper() != "LOGO":
                    continue
                image_run = image_by_id.get(image_finding.analysis_run_id)
                if image_run is None:
                    continue
                signal = by_id[image_run.evidence_id]
                label = image_finding.detector or "logo"
                meta = (
                    image_finding.metadata_json
                    if isinstance(image_finding.metadata_json, dict)
                    else {}
                )
                score = meta.get("logo_score")
                signal.logo_labels.add(
                    f"{label}:{score}" if score is not None else label
                )
                signal.logo_finding_ids.append(str(image_finding.id))

        signature_rows = list(
            await session.scalars(
                select(SignatureVerificationRun).where(
                    or_(
                        SignatureVerificationRun.questioned_evidence_id.in_(
                            evidence_ids
                        ),
                        SignatureVerificationRun.reference_evidence_id.in_(
                            evidence_ids
                        ),
                    )
                )
            )
        )
        for signature_run in signature_rows:
            left = signature_run.questioned_evidence_id
            right = signature_run.reference_evidence_id
            if left is None or right is None:
                continue
            if left not in by_id or right not in by_id:
                continue
            verdict = getattr(
                signature_run.verdict,
                "value",
                str(signature_run.verdict),
            )
            if verdict not in {"MATCH", "match"}:
                continue
            similarity = float(signature_run.similarity or 0.0)
            by_id[left].signature_pairs.append(
                (right, left, str(signature_run.id), similarity)
            )

        audio_runs = list(
            await session.scalars(
                select(AudioAnalysisRun).where(
                    AudioAnalysisRun.evidence_id.in_(evidence_ids)
                )
            )
        )
        if audio_runs:
            audio_run_ids = [item.id for item in audio_runs]
            audio_by_id = {item.id: item for item in audio_runs}
            audio_findings = list(
                await session.scalars(
                    select(AudioAIFinding).where(
                        AudioAIFinding.analysis_run_id.in_(audio_run_ids)
                    )
                )
            )
            for audio_finding in audio_findings:
                category = getattr(
                    audio_finding.category,
                    "value",
                    str(audio_finding.category),
                )
                if category.upper() != "REFERENCE_MISMATCH":
                    continue
                meta = (
                    audio_finding.metadata_json
                    if isinstance(audio_finding.metadata_json, dict)
                    else {}
                )
                similarity = float(
                    meta.get("similarity") or audio_finding.confidence or 0.0
                )
                if similarity < 0.7:
                    continue
                ref = meta.get("reference_evidence_id")
                audio_run = audio_by_id.get(audio_finding.analysis_run_id)
                if audio_run is None:
                    continue
                ref_id = audio_run.reference_evidence_id
                if ref:
                    try:
                        ref_id = UUID(str(ref))
                    except ValueError:
                        ref_id = audio_run.reference_evidence_id
                if ref_id is not None and ref_id in by_id:
                    by_id[audio_run.evidence_id].speaker_pairs.append(
                        (ref_id, str(audio_finding.id))
                    )

        timeline = await session.scalar(
            select(InvestigationTimeline)
            .where(
                InvestigationTimeline.case_id == case_id,
                InvestigationTimeline.status == "SUCCEEDED",
            )
            .order_by(InvestigationTimeline.created_at.desc())
            .limit(1)
        )
        if timeline is not None:
            events = list(
                await session.scalars(
                    select(TimelineEventRecord).where(
                        TimelineEventRecord.timeline_id == timeline.id,
                        TimelineEventRecord.evidence_id.in_(evidence_ids),
                        TimelineEventRecord.normalized_timestamp.is_not(None),
                    )
                )
            )
            for event in events:
                if event.evidence_id is None or event.normalized_timestamp is None:
                    continue
                by_id[event.evidence_id].timeline_timestamps.append(
                    (
                        event.event_id,
                        event.normalized_timestamp,
                        event.uncertainty_ms or 0,
                    )
                )

        return [by_id[item.id] for item in evidence_rows]

    def _match_all(
        self,
        case_id: UUID,
        signals: list[EvidenceSignals],
    ) -> list[EvidenceCorrelation]:
        results: list[EvidenceCorrelation] = []
        results.extend(
            self._match_exact_groups(
                case_id,
                signals,
                CorrelationType.SAME_HASH,
                lambda item: {item.sha256_hash},
                "sha256_hash",
            )
        )
        results.extend(
            self._match_exact_groups(
                case_id,
                signals,
                CorrelationType.SAME_EMAIL,
                lambda item: item.emails,
                "email",
            )
        )
        results.extend(
            self._match_exact_groups(
                case_id,
                signals,
                CorrelationType.SAME_PHONE,
                lambda item: item.phones,
                "phone",
            )
        )
        results.extend(
            self._match_exact_groups(
                case_id,
                signals,
                CorrelationType.SAME_QR,
                lambda item: item.qr_payloads,
                "qr_payload",
            )
        )
        results.extend(
            self._match_exact_groups(
                case_id,
                signals,
                CorrelationType.SAME_CAMERA,
                lambda item: item.camera_models,
                "camera_model",
            )
        )
        results.extend(
            self._match_exact_groups(
                case_id,
                signals,
                CorrelationType.SAME_DEVICE,
                lambda item: item.device_models,
                "device_model",
            )
        )
        results.extend(
            self._match_exact_groups(
                case_id,
                signals,
                CorrelationType.SAME_LOCATION,
                lambda item: item.locations,
                "location",
            )
        )
        results.extend(
            self._match_exact_groups(
                case_id,
                signals,
                CorrelationType.SAME_DOCUMENT,
                lambda item: item.document_ids,
                "document_id",
            )
        )
        results.extend(
            self._match_exact_groups(
                case_id,
                signals,
                CorrelationType.SHARED_IDENTIFIER,
                lambda item: item.identifiers,
                "identifier",
            )
        )
        results.extend(
            self._match_exact_groups(
                case_id,
                signals,
                CorrelationType.SAME_LOGO,
                lambda item: item.logo_labels,
                "logo",
            )
        )
        results.extend(self._match_shared_metadata(case_id, signals))
        results.extend(self._match_signatures(case_id, signals))
        results.extend(self._match_speakers(case_id, signals))
        results.extend(self._match_filenames(case_id, signals))
        results.extend(self._match_temporal(case_id, signals))
        return results

    def _match_exact_groups(
        self,
        case_id: UUID,
        signals: list[EvidenceSignals],
        correlation_type: CorrelationType,
        getter: Any,
        entity_label: str,
    ) -> list[EvidenceCorrelation]:
        results: list[EvidenceCorrelation] = []
        groups = group_by_value(signals, getter)
        for value, members in sorted(groups.items()):
            if len(members) < 2:
                continue
            ordered = sorted(members, key=lambda item: str(item.evidence_id))
            for index, left in enumerate(ordered):
                for right in ordered[index + 1 :]:
                    supports = (
                        support_entity(
                            "shared_value",
                            f"{entity_label}:{value}",
                            entity_label,
                            value,
                        ),
                    )
                    findings = tuple(
                        left.logo_finding_ids + right.logo_finding_ids
                        if correlation_type == CorrelationType.SAME_LOGO
                        else left.extraction_ids[:3] + right.extraction_ids[:3]
                    )
                    results.append(
                        self._make_correlation(
                            case_id=case_id,
                            left=left.evidence_id,
                            right=right.evidence_id,
                            correlation_type=correlation_type,
                            explanation=(
                                f"Evidence share the same {entity_label}: {value}."
                            ),
                            entities=(value,),
                            supports=supports,
                            findings=findings,
                            metadata={entity_label: value},
                        )
                    )
        return results

    def _match_shared_metadata(
        self,
        case_id: UUID,
        signals: list[EvidenceSignals],
    ) -> list[EvidenceCorrelation]:
        results: list[EvidenceCorrelation] = []
        ordered = sorted(signals, key=lambda item: str(item.evidence_id))
        for index, left in enumerate(ordered):
            for right in ordered[index + 1 :]:
                shared = {
                    key: left.metadata_fields[key]
                    for key in sorted(left.metadata_fields)
                    if key in right.metadata_fields
                    and left.metadata_fields[key] == right.metadata_fields[key]
                    and key not in {"camera_model", "device_model", "location"}
                }
                if not shared:
                    continue
                key, value = next(iter(shared.items()))
                results.append(
                    self._make_correlation(
                        case_id=case_id,
                        left=left.evidence_id,
                        right=right.evidence_id,
                        correlation_type=CorrelationType.SHARED_METADATA,
                        explanation=f"Evidence share metadata field {key}={value}.",
                        entities=(f"{key}:{value}",),
                        supports=(
                            support_entity(
                                "metadata",
                                f"metadata:{key}",
                                key,
                                value,
                            ),
                        ),
                        metadata={"shared_fields": shared},
                    )
                )
        return results

    def _match_signatures(
        self,
        case_id: UUID,
        signals: list[EvidenceSignals],
    ) -> list[EvidenceCorrelation]:
        results: list[EvidenceCorrelation] = []
        seen: set[str] = set()
        for signal in signals:
            for other_id, _self_id, run_id, similarity in signal.signature_pairs:
                key = correlation_key(
                    signal.evidence_id,
                    other_id,
                    CorrelationType.SAME_SIGNATURE.value,
                )
                if key in seen:
                    continue
                seen.add(key)
                results.append(
                    self._make_correlation(
                        case_id=case_id,
                        left=signal.evidence_id,
                        right=other_id,
                        correlation_type=CorrelationType.SAME_SIGNATURE,
                        explanation=(
                            "Signature verification reported a match between "
                            "questioned and reference evidence."
                        ),
                        entities=(run_id,),
                        supports=(
                            support_entity(
                                "signature_run",
                                run_id,
                                "signature_verification",
                                f"similarity={similarity}",
                            ),
                        ),
                        findings=(run_id,),
                        metadata={"similarity": similarity},
                    )
                )
        return results

    def _match_speakers(
        self,
        case_id: UUID,
        signals: list[EvidenceSignals],
    ) -> list[EvidenceCorrelation]:
        results: list[EvidenceCorrelation] = []
        seen: set[str] = set()
        for signal in signals:
            for other_id, support_id in signal.speaker_pairs:
                key = correlation_key(
                    signal.evidence_id,
                    other_id,
                    CorrelationType.SAME_AUDIO_SPEAKER.value,
                )
                if key in seen:
                    continue
                seen.add(key)
                results.append(
                    self._make_correlation(
                        case_id=case_id,
                        left=signal.evidence_id,
                        right=other_id,
                        correlation_type=CorrelationType.SAME_AUDIO_SPEAKER,
                        explanation=(
                            "Audio analysis linked these evidence items via "
                            "speaker/reference comparison."
                        ),
                        entities=(support_id,),
                        supports=(
                            support_entity(
                                "audio_analysis",
                                support_id,
                                "speaker_reference",
                            ),
                        ),
                        findings=(support_id,),
                    )
                )
        return results

    def _match_filenames(
        self,
        case_id: UUID,
        signals: list[EvidenceSignals],
    ) -> list[EvidenceCorrelation]:
        results: list[EvidenceCorrelation] = []
        for left, right, similarity in similar_filename_pairs(signals):
            results.append(
                self._make_correlation(
                    case_id=case_id,
                    left=left.evidence_id,
                    right=right.evidence_id,
                    correlation_type=CorrelationType.SIMILAR_FILENAME,
                    explanation=(
                        "Original filenames share overlapping tokens "
                        f"({left.original_filename} ~ {right.original_filename})."
                    ),
                    entities=(left.original_filename, right.original_filename),
                    supports=(
                        support_entity(
                            "filename",
                            left.original_filename,
                            "original_filename",
                            left.original_filename,
                        ),
                        support_entity(
                            "filename",
                            right.original_filename,
                            "original_filename",
                            right.original_filename,
                        ),
                    ),
                    metadata={"similarity": similarity},
                )
            )
        return results

    def _match_temporal(
        self,
        case_id: UUID,
        signals: list[EvidenceSignals],
    ) -> list[EvidenceCorrelation]:
        results: list[EvidenceCorrelation] = []
        ordered = sorted(signals, key=lambda item: str(item.evidence_id))
        for index, left in enumerate(ordered):
            if not left.timeline_timestamps:
                continue
            for right in ordered[index + 1 :]:
                if not right.timeline_timestamps:
                    continue
                overlap = self._find_temporal_overlap(
                    left.timeline_timestamps,
                    right.timeline_timestamps,
                )
                if overlap is None:
                    continue
                left_event, right_event, delta_ms = overlap
                results.append(
                    self._make_correlation(
                        case_id=case_id,
                        left=left.evidence_id,
                        right=right.evidence_id,
                        correlation_type=CorrelationType.TEMPORAL_OVERLAP,
                        explanation=(
                            "Timeline metadata timestamps overlap within "
                            f"uncertainty windows (delta_ms={delta_ms})."
                        ),
                        entities=(left_event, right_event),
                        supports=(
                            support_entity(
                                "timeline_event",
                                left_event,
                                "timeline_event",
                                left_event,
                            ),
                            support_entity(
                                "timeline_event",
                                right_event,
                                "timeline_event",
                                right_event,
                            ),
                        ),
                        findings=(left_event, right_event),
                        metadata={"delta_ms": delta_ms},
                    )
                )
        return results

    @staticmethod
    def _find_temporal_overlap(
        left_events: list[tuple[str, Any, int]],
        right_events: list[tuple[str, Any, int]],
    ) -> tuple[str, str, int] | None:
        best: tuple[str, str, int] | None = None
        for left_id, left_ts, left_unc in left_events:
            if not isinstance(left_ts, datetime):
                continue
            for right_id, right_ts, right_unc in right_events:
                if not isinstance(right_ts, datetime):
                    continue
                window = timedelta(milliseconds=max(left_unc, right_unc, 60_000))
                delta = abs(left_ts - right_ts)
                if delta <= window:
                    delta_ms = int(delta.total_seconds() * 1000)
                    if best is None or delta_ms < best[2]:
                        best = (left_id, right_id, delta_ms)
        return best

    def _make_correlation(
        self,
        *,
        case_id: UUID,
        left: UUID,
        right: UUID,
        correlation_type: CorrelationType,
        explanation: str,
        entities: tuple[str, ...] = (),
        supports: tuple[CorrelationSupport, ...] = (),
        findings: tuple[str, ...] = (),
        metadata: dict[str, Any] | None = None,
    ) -> EvidenceCorrelation:
        a, b = canonical_pair(left, right)
        return EvidenceCorrelation(
            correlation_id=correlation_key(a, b, correlation_type.value),
            case_id=case_id,
            left_evidence_id=a,
            right_evidence_id=b,
            correlation_type=correlation_type,
            score=score_for(correlation_type),
            confidence=confidence_for(correlation_type),
            explanation=explanation,
            supporting_findings=findings,
            supporting_metadata=metadata or {},
            supporting_entities=entities,
            supports=supports,
            provenance=build_provenance(
                case_id=case_id,
                left_evidence_id=a,
                right_evidence_id=b,
                correlation_type=correlation_type.value,
            ),
        )

    @staticmethod
    def _deduplicate(
        correlations: list[EvidenceCorrelation],
    ) -> list[EvidenceCorrelation]:
        unique: dict[str, EvidenceCorrelation] = {}
        for item in correlations:
            existing = unique.get(item.correlation_id)
            if existing is None or item.score > existing.score:
                unique[item.correlation_id] = item
        return list(unique.values())
