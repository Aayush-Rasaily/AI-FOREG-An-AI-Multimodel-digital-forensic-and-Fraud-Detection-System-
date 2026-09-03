"""Deterministic entity resolution from existing Phase 1-7B outputs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.correlation.matchers import location_key, metadata_scalar, nested_dict
from backend.app.correlation.models import CorrelationRunStatus, CorrelationType
from backend.app.entities.confidence import (
    boost_confidence,
    confidence_for_entity,
    confidence_for_relationship,
)
from backend.app.entities.graph import build_graph
from backend.app.entities.models import (
    CanonicalEntity,
    EntityBuildResult,
    EntityEdge,
    EntitySupport,
    EntityType,
    RelationshipType,
)
from backend.app.entities.normalizer import (
    domains_from_urls,
    extract_addresses,
    extract_bank_accounts,
    extract_emails,
    extract_identifiers,
    extract_ips,
    extract_phones,
    extract_urls,
    extract_wallets,
    media_entity_type_for_mime,
    normalize_domain,
    normalize_email,
    normalize_generic,
    normalize_hash,
    normalize_ip,
    normalize_location,
    normalize_phone,
    normalize_wallet,
    normalize_website,
)
from backend.app.entities.policy import ENGINE_VERSION, POLICY_VERSION
from backend.app.entities.provenance import (
    build_edge_provenance,
    build_entity_provenance,
    build_run_provenance,
    canonical_entity_key,
    format_canonical_id,
    relationship_key,
)
from backend.app.extraction.models import ExtractionType
from backend.app.models.case import Case
from backend.app.models.correlation import (
    CorrelationAnalysisRun,
    EvidenceCorrelationRecord,
)
from backend.app.models.evidence import Evidence
from backend.app.models.extraction import ExtractionRecord
from backend.app.models.fusion import FusionAnalysisRun
from backend.app.models.image_ai import ImageAIFinding, ImageAnalysisRun
from backend.app.models.signature_ai import SignatureVerificationRun
from backend.app.models.timeline import InvestigationTimeline, TimelineEventRecord
from backend.app.timeline.models import TimelineRunStatus


@dataclass
class _EntityDraft:
    entity_type: EntityType
    normalized_key: str
    display_name: str
    evidence_ids: set[UUID] = field(default_factory=set)
    extraction_ids: set[str] = field(default_factory=set)
    finding_ids: set[str] = field(default_factory=set)
    correlation_ids: set[str] = field(default_factory=set)
    timeline_ids: set[str] = field(default_factory=set)
    fusion_ids: set[str] = field(default_factory=set)
    metadata_fields: set[str] = field(default_factory=set)
    supports: list[EntitySupport] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class _EdgeDraft:
    source_key: str
    target_key: str
    relationship_type: RelationshipType
    explanation: str
    evidence_ids: set[UUID] = field(default_factory=set)
    extraction_ids: set[str] = field(default_factory=set)
    finding_ids: set[str] = field(default_factory=set)
    correlation_ids: set[str] = field(default_factory=set)
    timeline_ids: set[str] = field(default_factory=set)
    fusion_ids: set[str] = field(default_factory=set)
    supports: list[EntitySupport] = field(default_factory=list)


class EntityResolver:
    """Merge existing case artifacts into canonical entities and relationships."""

    async def resolve(
        self,
        session: AsyncSession,
        case: Case,
    ) -> EntityBuildResult:
        evidence_rows = list(
            await session.scalars(select(Evidence).where(Evidence.case_id == case.id))
        )
        drafts: dict[str, _EntityDraft] = {}
        edges: dict[str, _EdgeDraft] = {}
        media_keys: dict[UUID, str] = {}

        for evidence in sorted(evidence_rows, key=lambda item: str(item.id)):
            media_type = EntityType(media_entity_type_for_mime(evidence.mime_type))
            media_key = self._upsert(
                drafts,
                entity_type=media_type,
                normalized_key=str(evidence.id),
                display_name=evidence.original_filename or evidence.evidence_number,
                evidence_id=evidence.id,
                support=EntitySupport(
                    support_kind="evidence",
                    support_id=str(evidence.id),
                    label="evidence",
                    value=evidence.evidence_number,
                ),
                attributes={
                    "evidence_number": evidence.evidence_number,
                    "mime_type": evidence.mime_type,
                    "filename": evidence.original_filename,
                },
            )
            media_keys[evidence.id] = media_key

            hash_key = self._upsert(
                drafts,
                entity_type=EntityType.FILE_HASH,
                normalized_key=normalize_hash(evidence.sha256_hash),
                display_name=evidence.sha256_hash[:16],
                evidence_id=evidence.id,
                support=EntitySupport(
                    support_kind="hash",
                    support_id=evidence.sha256_hash,
                    label="sha256",
                    value=evidence.sha256_hash,
                ),
                metadata_fields={"sha256_hash"},
            )
            self._link(
                edges,
                source_key=media_key,
                target_key=hash_key,
                relationship_type=RelationshipType.DERIVED_FROM,
                explanation="Evidence content hash links media to file-hash entity.",
                evidence_id=evidence.id,
                support=EntitySupport(
                    support_kind="hash",
                    support_id=evidence.sha256_hash,
                    label="sha256",
                    value=evidence.sha256_hash,
                ),
            )

            metadata = (
                evidence.metadata_json
                if isinstance(evidence.metadata_json, dict)
                else {}
            )
            self._ingest_metadata(
                drafts,
                edges,
                evidence=evidence,
                media_key=media_key,
                metadata=metadata,
            )

        await self._ingest_extracted_text(
            session,
            drafts,
            edges,
            evidence_rows=evidence_rows,
            media_keys=media_keys,
        )
        await self._ingest_image_findings(
            session,
            drafts,
            edges,
            evidence_rows=evidence_rows,
            media_keys=media_keys,
        )
        await self._ingest_signatures(
            session,
            drafts,
            edges,
            evidence_rows=evidence_rows,
            media_keys=media_keys,
        )
        await self._ingest_correlations(
            session,
            drafts,
            edges,
            case_id=case.id,
            media_keys=media_keys,
        )
        await self._ingest_timeline(session, drafts, case_id=case.id)
        await self._ingest_fusion(
            session,
            drafts,
            evidence_ids=[item.id for item in evidence_rows],
        )

        entities = self._materialize_entities(case.id, drafts)
        key_to_canonical = {
            canonical_entity_key(item.entity_type.value, item.normalized_key): (
                item.canonical_id
            )
            for item in entities
        }
        relationships = self._materialize_edges(case.id, edges, key_to_canonical)
        provenance = build_run_provenance(
            case_id=case.id,
            case_number=case.case_number,
            evidence_count=len(evidence_rows),
            entity_count=len(entities),
            relationship_count=len(relationships),
        )
        metadata = {
            "entity_count": len(entities),
            "relationship_count": len(relationships),
            "evidence_count": len(evidence_rows),
            "engine_version": ENGINE_VERSION,
            "policy_version": POLICY_VERSION,
        }
        graph = build_graph(
            entities,
            relationships,
            provenance=provenance,
            metadata=metadata,
        )
        return EntityBuildResult(
            entities=entities,
            relationships=relationships,
            graph=graph,
            provenance=provenance,
            metadata=metadata,
        )

    def _ingest_metadata(
        self,
        drafts: dict[str, _EntityDraft],
        edges: dict[str, _EdgeDraft],
        *,
        evidence: Evidence,
        media_key: str,
        metadata: dict[str, Any],
    ) -> None:
        exif = nested_dict(metadata, "exif")
        camera = metadata_scalar(
            exif,
            "Model",
            "CameraModel",
            "camera_model",
            "Make",
        ) or metadata_scalar(metadata, "camera_model")
        if camera:
            camera_key = self._upsert(
                drafts,
                entity_type=EntityType.CAMERA,
                normalized_key=normalize_generic(camera),
                display_name=camera,
                evidence_id=evidence.id,
                support=EntitySupport(
                    support_kind="metadata",
                    support_id=str(evidence.id),
                    label="camera_model",
                    value=camera,
                ),
                metadata_fields={"camera_model"},
            )
            self._link(
                edges,
                source_key=media_key,
                target_key=camera_key,
                relationship_type=RelationshipType.CAPTURED_BY,
                explanation="EXIF/camera metadata links media to camera entity.",
                evidence_id=evidence.id,
            )

        device = metadata_scalar(
            exif,
            "DeviceModel",
            "device_model",
            "Software",
        ) or metadata_scalar(metadata, "device_model")
        if device:
            device_key = self._upsert(
                drafts,
                entity_type=EntityType.DEVICE,
                normalized_key=normalize_generic(device),
                display_name=device,
                evidence_id=evidence.id,
                support=EntitySupport(
                    support_kind="metadata",
                    support_id=str(evidence.id),
                    label="device_model",
                    value=device,
                ),
                metadata_fields={"device_model"},
            )
            self._link(
                edges,
                source_key=media_key,
                target_key=device_key,
                relationship_type=RelationshipType.USES,
                explanation="Device metadata links media to device entity.",
                evidence_id=evidence.id,
            )

        loc = location_key(metadata)
        if loc:
            location_entity = self._upsert(
                drafts,
                entity_type=EntityType.LOCATION,
                normalized_key=normalize_location(loc),
                display_name=loc,
                evidence_id=evidence.id,
                support=EntitySupport(
                    support_kind="metadata",
                    support_id=str(evidence.id),
                    label="gps",
                    value=loc,
                ),
                metadata_fields={"location"},
            )
            self._link(
                edges,
                source_key=media_key,
                target_key=location_entity,
                relationship_type=RelationshipType.LOCATED_AT,
                explanation="GPS/metadata location links media to location entity.",
                evidence_id=evidence.id,
            )

        creator = metadata_scalar(
            nested_dict(metadata, "processing"),
            "creator",
            "author",
        )
        if creator:
            org_key = self._upsert(
                drafts,
                entity_type=EntityType.ORGANIZATION,
                normalized_key=normalize_generic(creator),
                display_name=creator,
                evidence_id=evidence.id,
                support=EntitySupport(
                    support_kind="metadata",
                    support_id=str(evidence.id),
                    label="creator",
                    value=creator,
                ),
                metadata_fields={"creator"},
            )
            self._link(
                edges,
                source_key=org_key,
                target_key=media_key,
                relationship_type=RelationshipType.CREATED,
                explanation=(
                    "Processing creator/author metadata links organization to media."
                ),
                evidence_id=evidence.id,
            )

        vehicle = metadata_scalar(metadata, "vehicle", "vehicle_id", "license_plate")
        if vehicle:
            self._upsert(
                drafts,
                entity_type=EntityType.VEHICLE,
                normalized_key=normalize_generic(vehicle),
                display_name=vehicle,
                evidence_id=evidence.id,
                support=EntitySupport(
                    support_kind="metadata",
                    support_id=str(evidence.id),
                    label="vehicle",
                    value=vehicle,
                ),
                metadata_fields={"vehicle"},
            )

    async def _ingest_extracted_text(
        self,
        session: AsyncSession,
        drafts: dict[str, _EntityDraft],
        edges: dict[str, _EdgeDraft],
        *,
        evidence_rows: list[Evidence],
        media_keys: dict[UUID, str],
    ) -> None:
        evidence_ids = [item.id for item in evidence_rows]
        if not evidence_ids:
            return
        rows = list(
            await session.scalars(
                select(ExtractionRecord).where(
                    ExtractionRecord.evidence_id.in_(evidence_ids)
                )
            )
        )
        for record in sorted(rows, key=lambda item: str(item.id)):
            content = (record.content or "").strip()
            if not content:
                continue
            media_key = media_keys.get(record.evidence_id)
            if media_key is None:
                continue
            self._ingest_text_signals(
                drafts,
                edges,
                evidence_id=record.evidence_id,
                media_key=media_key,
                content=content,
                extraction_id=str(record.id),
                extraction_type=record.extraction_type,
            )

    def _ingest_text_signals(
        self,
        drafts: dict[str, _EntityDraft],
        edges: dict[str, _EdgeDraft],
        *,
        evidence_id: UUID,
        media_key: str,
        content: str,
        extraction_id: str,
        extraction_type: ExtractionType,
    ) -> None:
        supports_base = EntitySupport(
            support_kind="extraction",
            support_id=extraction_id,
            label=extraction_type.value,
            value=content[:256],
        )
        if extraction_type in {
            ExtractionType.TEXT,
            ExtractionType.LINE,
            ExtractionType.WORD,
            ExtractionType.PAGE,
        }:
            for email in extract_emails(content):
                key = self._upsert(
                    drafts,
                    entity_type=EntityType.EMAIL,
                    normalized_key=normalize_email(email),
                    display_name=email,
                    evidence_id=evidence_id,
                    extraction_id=extraction_id,
                    support=supports_base,
                )
                self._link(
                    edges,
                    source_key=media_key,
                    target_key=key,
                    relationship_type=RelationshipType.CONTAINS,
                    explanation="OCR/text extraction contains email entity.",
                    evidence_id=evidence_id,
                    extraction_id=extraction_id,
                    support=supports_base,
                )
            for phone in extract_phones(content):
                key = self._upsert(
                    drafts,
                    entity_type=EntityType.PHONE,
                    normalized_key=normalize_phone(phone),
                    display_name=phone,
                    evidence_id=evidence_id,
                    extraction_id=extraction_id,
                    support=supports_base,
                )
                self._link(
                    edges,
                    source_key=media_key,
                    target_key=key,
                    relationship_type=RelationshipType.CONTAINS,
                    explanation="OCR/text extraction contains phone entity.",
                    evidence_id=evidence_id,
                    extraction_id=extraction_id,
                    support=supports_base,
                )
            urls = extract_urls(content)
            for url in urls:
                website_key = self._upsert(
                    drafts,
                    entity_type=EntityType.WEBSITE,
                    normalized_key=normalize_website(url),
                    display_name=url,
                    evidence_id=evidence_id,
                    extraction_id=extraction_id,
                    support=supports_base,
                )
                self._link(
                    edges,
                    source_key=media_key,
                    target_key=website_key,
                    relationship_type=RelationshipType.REFERENCES,
                    explanation="OCR/text extraction references website entity.",
                    evidence_id=evidence_id,
                    extraction_id=extraction_id,
                    support=supports_base,
                )
            for domain in domains_from_urls(urls):
                domain_key = self._upsert(
                    drafts,
                    entity_type=EntityType.DOMAIN,
                    normalized_key=normalize_domain(domain),
                    display_name=domain,
                    evidence_id=evidence_id,
                    extraction_id=extraction_id,
                    support=supports_base,
                )
                self._link(
                    edges,
                    source_key=media_key,
                    target_key=domain_key,
                    relationship_type=RelationshipType.REFERENCES,
                    explanation="OCR/text extraction references domain entity.",
                    evidence_id=evidence_id,
                    extraction_id=extraction_id,
                    support=supports_base,
                )
            for ip in extract_ips(content):
                key = self._upsert(
                    drafts,
                    entity_type=EntityType.IP_ADDRESS,
                    normalized_key=normalize_ip(ip),
                    display_name=ip,
                    evidence_id=evidence_id,
                    extraction_id=extraction_id,
                    support=supports_base,
                )
                self._link(
                    edges,
                    source_key=media_key,
                    target_key=key,
                    relationship_type=RelationshipType.REFERENCES,
                    explanation="OCR/text extraction references IP address entity.",
                    evidence_id=evidence_id,
                    extraction_id=extraction_id,
                    support=supports_base,
                )
            for wallet in extract_wallets(content):
                key = self._upsert(
                    drafts,
                    entity_type=EntityType.CRYPTO_WALLET,
                    normalized_key=normalize_wallet(wallet),
                    display_name=wallet,
                    evidence_id=evidence_id,
                    extraction_id=extraction_id,
                    support=supports_base,
                )
                self._link(
                    edges,
                    source_key=media_key,
                    target_key=key,
                    relationship_type=RelationshipType.REFERENCES,
                    explanation="OCR/text extraction references crypto wallet entity.",
                    evidence_id=evidence_id,
                    extraction_id=extraction_id,
                    support=supports_base,
                )
            for account in extract_bank_accounts(content):
                key = self._upsert(
                    drafts,
                    entity_type=EntityType.BANK_ACCOUNT,
                    normalized_key=account,
                    display_name=account,
                    evidence_id=evidence_id,
                    extraction_id=extraction_id,
                    support=supports_base,
                )
                self._link(
                    edges,
                    source_key=media_key,
                    target_key=key,
                    relationship_type=RelationshipType.REFERENCES,
                    explanation="OCR/text extraction references bank account entity.",
                    evidence_id=evidence_id,
                    extraction_id=extraction_id,
                    support=supports_base,
                )
            for address in extract_addresses(content):
                key = self._upsert(
                    drafts,
                    entity_type=EntityType.ADDRESS,
                    normalized_key=normalize_generic(address),
                    display_name=address,
                    evidence_id=evidence_id,
                    extraction_id=extraction_id,
                    support=supports_base,
                )
                self._link(
                    edges,
                    source_key=media_key,
                    target_key=key,
                    relationship_type=RelationshipType.LOCATED_AT,
                    explanation="OCR/text extraction references address entity.",
                    evidence_id=evidence_id,
                    extraction_id=extraction_id,
                    support=supports_base,
                )
            for identifier in extract_identifiers(content):
                key = self._upsert(
                    drafts,
                    entity_type=EntityType.DOCUMENT,
                    normalized_key=normalize_generic(identifier),
                    display_name=identifier,
                    evidence_id=evidence_id,
                    extraction_id=extraction_id,
                    support=supports_base,
                    attributes={"document_id": identifier},
                )
                self._link(
                    edges,
                    source_key=media_key,
                    target_key=key,
                    relationship_type=RelationshipType.REFERENCES,
                    explanation=(
                        "OCR/text extraction references document identifier entity."
                    ),
                    evidence_id=evidence_id,
                    extraction_id=extraction_id,
                    support=supports_base,
                )

        if extraction_type == ExtractionType.QR_CODE:
            key = self._upsert(
                drafts,
                entity_type=EntityType.QR_CODE,
                normalized_key=normalize_generic(content),
                display_name=content[:64],
                evidence_id=evidence_id,
                extraction_id=extraction_id,
                support=supports_base,
            )
            self._link(
                edges,
                source_key=media_key,
                target_key=key,
                relationship_type=RelationshipType.CONTAINS,
                explanation="QR extraction links media to QR-code entity.",
                evidence_id=evidence_id,
                extraction_id=extraction_id,
                support=supports_base,
            )

        if extraction_type == ExtractionType.LOGO_REGION:
            key = self._upsert(
                drafts,
                entity_type=EntityType.LOGO,
                normalized_key=normalize_generic(content or f"logo:{extraction_id}"),
                display_name=content or f"logo:{extraction_id}",
                evidence_id=evidence_id,
                extraction_id=extraction_id,
                support=supports_base,
            )
            self._link(
                edges,
                source_key=media_key,
                target_key=key,
                relationship_type=RelationshipType.CONTAINS,
                explanation="Logo-region extraction links media to logo entity.",
                evidence_id=evidence_id,
                extraction_id=extraction_id,
                support=supports_base,
            )

        if extraction_type == ExtractionType.SIGNATURE_REGION:
            key = self._upsert(
                drafts,
                entity_type=EntityType.SIGNATURE,
                normalized_key=normalize_generic(
                    content or f"signature:{extraction_id}"
                ),
                display_name=content or f"signature:{extraction_id}",
                evidence_id=evidence_id,
                extraction_id=extraction_id,
                support=supports_base,
            )
            self._link(
                edges,
                source_key=media_key,
                target_key=key,
                relationship_type=RelationshipType.SIGNED_BY,
                explanation=(
                    "Signature-region extraction links media to signature entity."
                ),
                evidence_id=evidence_id,
                extraction_id=extraction_id,
                support=supports_base,
            )

        if extraction_type == ExtractionType.FACE_REGION:
            key = self._upsert(
                drafts,
                entity_type=EntityType.PERSON,
                normalized_key=normalize_generic(content or f"person:{extraction_id}"),
                display_name=content or f"person:{extraction_id}",
                evidence_id=evidence_id,
                extraction_id=extraction_id,
                support=supports_base,
            )
            self._link(
                edges,
                source_key=media_key,
                target_key=key,
                relationship_type=RelationshipType.CONTAINS,
                explanation="Face-region extraction links media to person entity.",
                evidence_id=evidence_id,
                extraction_id=extraction_id,
                support=supports_base,
            )

    async def _ingest_image_findings(
        self,
        session: AsyncSession,
        drafts: dict[str, _EntityDraft],
        edges: dict[str, _EdgeDraft],
        *,
        evidence_rows: list[Evidence],
        media_keys: dict[UUID, str],
    ) -> None:
        evidence_ids = [item.id for item in evidence_rows]
        if not evidence_ids:
            return
        runs = list(
            await session.scalars(
                select(ImageAnalysisRun).where(
                    ImageAnalysisRun.evidence_id.in_(evidence_ids)
                )
            )
        )
        run_ids = [item.id for item in runs]
        if not run_ids:
            return
        findings = list(
            await session.scalars(
                select(ImageAIFinding).where(
                    ImageAIFinding.analysis_run_id.in_(run_ids)
                )
            )
        )
        for finding in sorted(findings, key=lambda item: str(item.id)):
            category = str(getattr(finding.category, "value", finding.category)).upper()
            if category != "LOGO":
                continue
            media_key = media_keys.get(finding.evidence_id)
            if media_key is None:
                continue
            meta = (
                finding.metadata_json
                if isinstance(finding.metadata_json, dict)
                else {}
            )
            label = str(
                meta.get("logo_label")
                or meta.get("label")
                or finding.description
                or f"logo:{finding.id}"
            )
            key = self._upsert(
                drafts,
                entity_type=EntityType.LOGO,
                normalized_key=normalize_generic(label),
                display_name=label[:128],
                evidence_id=finding.evidence_id,
                finding_id=str(finding.id),
                support=EntitySupport(
                    support_kind="image_ai_finding",
                    support_id=str(finding.id),
                    label="logo",
                    value=label[:256],
                ),
            )
            self._link(
                edges,
                source_key=media_key,
                target_key=key,
                relationship_type=RelationshipType.CONTAINS,
                explanation="Image AI logo finding links media to logo entity.",
                evidence_id=finding.evidence_id,
                finding_id=str(finding.id),
            )

    async def _ingest_signatures(
        self,
        session: AsyncSession,
        drafts: dict[str, _EntityDraft],
        edges: dict[str, _EdgeDraft],
        *,
        evidence_rows: list[Evidence],
        media_keys: dict[UUID, str],
    ) -> None:
        evidence_ids = [item.id for item in evidence_rows]
        if not evidence_ids:
            return
        runs = list(
            await session.scalars(
                select(SignatureVerificationRun).where(
                    SignatureVerificationRun.questioned_evidence_id.in_(evidence_ids)
                )
            )
        )
        for run in sorted(runs, key=lambda item: str(item.id)):
            verdict = str(getattr(run.verdict, "value", run.verdict)).upper()
            if verdict != "MATCH":
                continue
            if run.questioned_evidence_id is None:
                continue
            sig_key = self._upsert(
                drafts,
                entity_type=EntityType.SIGNATURE,
                normalized_key=normalize_generic(f"sig-run:{run.id}"),
                display_name=f"signature:{run.id}",
                evidence_id=run.questioned_evidence_id,
                finding_id=str(run.id),
                support=EntitySupport(
                    support_kind="signature_run",
                    support_id=str(run.id),
                    label="signature_match",
                    value=str(run.similarity),
                ),
            )
            if run.reference_evidence_id is not None:
                drafts[sig_key].evidence_ids.add(run.reference_evidence_id)
            left = media_keys.get(run.questioned_evidence_id)
            right = (
                media_keys.get(run.reference_evidence_id)
                if run.reference_evidence_id is not None
                else None
            )
            if left:
                self._link(
                    edges,
                    source_key=left,
                    target_key=sig_key,
                    relationship_type=RelationshipType.SIGNED_BY,
                    explanation=(
                        "Signature verification MATCH links questioned media "
                        "to signature."
                    ),
                    evidence_id=run.questioned_evidence_id,
                    finding_id=str(run.id),
                )
            if right and run.reference_evidence_id is not None:
                self._link(
                    edges,
                    source_key=right,
                    target_key=sig_key,
                    relationship_type=RelationshipType.SIGNED_BY,
                    explanation=(
                        "Signature verification MATCH links reference media "
                        "to signature."
                    ),
                    evidence_id=run.reference_evidence_id,
                    finding_id=str(run.id),
                )
            if left and right:
                self._link(
                    edges,
                    source_key=left,
                    target_key=right,
                    relationship_type=RelationshipType.RELATED_TO,
                    explanation=(
                        "Signature MATCH relates questioned and reference "
                        "evidence media."
                    ),
                    evidence_id=run.questioned_evidence_id,
                    finding_id=str(run.id),
                )

    async def _ingest_correlations(
        self,
        session: AsyncSession,
        drafts: dict[str, _EntityDraft],
        edges: dict[str, _EdgeDraft],
        *,
        case_id: UUID,
        media_keys: dict[UUID, str],
    ) -> None:
        latest = (
            await session.scalars(
                select(CorrelationAnalysisRun)
                .where(
                    CorrelationAnalysisRun.case_id == case_id,
                    CorrelationAnalysisRun.status == CorrelationRunStatus.SUCCEEDED,
                )
                .order_by(CorrelationAnalysisRun.created_at.desc())
                .limit(1)
            )
        ).first()
        if latest is None:
            return
        correlations = list(
            await session.scalars(
                select(EvidenceCorrelationRecord).where(
                    EvidenceCorrelationRecord.analysis_run_id == latest.id
                )
            )
        )
        type_map: dict[CorrelationType, RelationshipType] = {
            CorrelationType.SAME_HASH: RelationshipType.DUPLICATE_OF,
            CorrelationType.SAME_EMAIL: RelationshipType.RELATED_TO,
            CorrelationType.SAME_PHONE: RelationshipType.RELATED_TO,
            CorrelationType.SAME_DEVICE: RelationshipType.USES,
            CorrelationType.SAME_CAMERA: RelationshipType.CAPTURED_BY,
            CorrelationType.SAME_SIGNATURE: RelationshipType.SIGNED_BY,
            CorrelationType.SAME_LOGO: RelationshipType.RELATED_TO,
            CorrelationType.SAME_QR: RelationshipType.RELATED_TO,
            CorrelationType.SAME_AUDIO_SPEAKER: RelationshipType.RELATED_TO,
            CorrelationType.SAME_LOCATION: RelationshipType.LOCATED_AT,
            CorrelationType.SAME_DOCUMENT: RelationshipType.REFERENCES,
            CorrelationType.SIMILAR_FILENAME: RelationshipType.RELATED_TO,
            CorrelationType.TEMPORAL_OVERLAP: RelationshipType.RELATED_TO,
            CorrelationType.SHARED_METADATA: RelationshipType.RELATED_TO,
            CorrelationType.SHARED_IDENTIFIER: RelationshipType.REFERENCES,
        }
        for item in sorted(correlations, key=lambda row: row.correlation_id):
            left = media_keys.get(item.left_evidence_id)
            right = media_keys.get(item.right_evidence_id)
            if left is None or right is None:
                continue
            rel_type = type_map.get(item.correlation_type, RelationshipType.RELATED_TO)
            source, target = left, right
            if str(item.left_evidence_id) > str(item.right_evidence_id):
                source, target = right, left
            self._link(
                edges,
                source_key=source,
                target_key=target,
                relationship_type=rel_type,
                explanation=(
                    f"Correlation {item.correlation_type.value} links "
                    "evidence media entities."
                ),
                evidence_id=item.left_evidence_id,
                correlation_id=item.correlation_id,
                support=EntitySupport(
                    support_kind="correlation",
                    support_id=item.correlation_id,
                    label=item.correlation_type.value,
                    value=str(item.score),
                ),
            )
            for entity_value in item.supporting_entities_json or []:
                email_key = canonical_entity_key(
                    EntityType.EMAIL.value,
                    normalize_email(str(entity_value)),
                )
                draft = drafts.get(email_key)
                if draft is not None:
                    draft.correlation_ids.add(item.correlation_id)

    async def _ingest_timeline(
        self,
        session: AsyncSession,
        drafts: dict[str, _EntityDraft],
        *,
        case_id: UUID,
    ) -> None:
        latest = (
            await session.scalars(
                select(InvestigationTimeline)
                .where(
                    InvestigationTimeline.case_id == case_id,
                    InvestigationTimeline.status == TimelineRunStatus.SUCCEEDED,
                )
                .order_by(InvestigationTimeline.created_at.desc())
                .limit(1)
            )
        ).first()
        if latest is None:
            return
        events = list(
            await session.scalars(
                select(TimelineEventRecord).where(
                    TimelineEventRecord.timeline_id == latest.id
                )
            )
        )
        for event in events:
            for draft in drafts.values():
                if event.evidence_id in draft.evidence_ids:
                    draft.timeline_ids.add(event.event_id)

    async def _ingest_fusion(
        self,
        session: AsyncSession,
        drafts: dict[str, _EntityDraft],
        *,
        evidence_ids: list[UUID],
    ) -> None:
        if not evidence_ids:
            return
        runs = list(
            await session.scalars(
                select(FusionAnalysisRun).where(
                    FusionAnalysisRun.evidence_id.in_(evidence_ids)
                )
            )
        )
        by_evidence: dict[UUID, list[str]] = {}
        for run in runs:
            by_evidence.setdefault(run.evidence_id, []).append(str(run.id))
        for draft in drafts.values():
            for evidence_id in draft.evidence_ids:
                for fusion_id in by_evidence.get(evidence_id, []):
                    draft.fusion_ids.add(fusion_id)

    def _upsert(
        self,
        drafts: dict[str, _EntityDraft],
        *,
        entity_type: EntityType,
        normalized_key: str,
        display_name: str,
        evidence_id: UUID,
        support: EntitySupport,
        extraction_id: str | None = None,
        finding_id: str | None = None,
        correlation_id: str | None = None,
        timeline_id: str | None = None,
        fusion_id: str | None = None,
        metadata_fields: set[str] | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> str:
        key = canonical_entity_key(entity_type.value, normalized_key)
        draft = drafts.get(key)
        if draft is None:
            draft = _EntityDraft(
                entity_type=entity_type,
                normalized_key=normalized_key,
                display_name=display_name,
            )
            drafts[key] = draft
        draft.evidence_ids.add(evidence_id)
        draft.supports.append(support)
        if extraction_id:
            draft.extraction_ids.add(extraction_id)
        if finding_id:
            draft.finding_ids.add(finding_id)
        if correlation_id:
            draft.correlation_ids.add(correlation_id)
        if timeline_id:
            draft.timeline_ids.add(timeline_id)
        if fusion_id:
            draft.fusion_ids.add(fusion_id)
        if metadata_fields:
            draft.metadata_fields.update(metadata_fields)
        if attributes:
            draft.attributes.update(attributes)
        return key

    def _link(
        self,
        edges: dict[str, _EdgeDraft],
        *,
        source_key: str,
        target_key: str,
        relationship_type: RelationshipType,
        explanation: str,
        evidence_id: UUID,
        support: EntitySupport | None = None,
        extraction_id: str | None = None,
        finding_id: str | None = None,
        correlation_id: str | None = None,
        timeline_id: str | None = None,
        fusion_id: str | None = None,
    ) -> None:
        if source_key == target_key:
            return
        edge_id = relationship_key(source_key, target_key, relationship_type.value)
        draft = edges.get(edge_id)
        if draft is None:
            draft = _EdgeDraft(
                source_key=source_key,
                target_key=target_key,
                relationship_type=relationship_type,
                explanation=explanation,
            )
            edges[edge_id] = draft
        draft.evidence_ids.add(evidence_id)
        if support is not None:
            draft.supports.append(support)
        if extraction_id:
            draft.extraction_ids.add(extraction_id)
        if finding_id:
            draft.finding_ids.add(finding_id)
        if correlation_id:
            draft.correlation_ids.add(correlation_id)
        if timeline_id:
            draft.timeline_ids.add(timeline_id)
        if fusion_id:
            draft.fusion_ids.add(fusion_id)

    def _materialize_entities(
        self,
        case_id: UUID,
        drafts: dict[str, _EntityDraft],
    ) -> tuple[CanonicalEntity, ...]:
        ordered_keys = sorted(
            drafts.keys(),
            key=lambda key: (
                drafts[key].entity_type.value,
                drafts[key].normalized_key,
                min((str(item) for item in drafts[key].evidence_ids), default=""),
            ),
        )
        entities: list[CanonicalEntity] = []
        for index, key in enumerate(ordered_keys, start=1):
            draft = drafts[key]
            support_count = max(len(draft.evidence_ids), 1)
            confidence = boost_confidence(
                confidence_for_entity(draft.entity_type),
                support_count,
            )
            entities.append(
                CanonicalEntity(
                    canonical_id=format_canonical_id(index),
                    case_id=case_id,
                    entity_type=draft.entity_type,
                    display_name=draft.display_name,
                    normalized_key=draft.normalized_key,
                    confidence=confidence,
                    support_count=support_count,
                    evidence_ids=tuple(sorted(draft.evidence_ids, key=str)),
                    supports=tuple(draft.supports),
                    provenance=build_entity_provenance(
                        case_id=case_id,
                        entity_type=draft.entity_type.value,
                        normalized_key=draft.normalized_key,
                        evidence_ids=[str(item) for item in draft.evidence_ids],
                        extraction_ids=list(draft.extraction_ids),
                        finding_ids=list(draft.finding_ids),
                        correlation_ids=list(draft.correlation_ids),
                        timeline_ids=list(draft.timeline_ids),
                        fusion_ids=list(draft.fusion_ids),
                        metadata_fields=list(draft.metadata_fields),
                    ),
                    attributes=dict(draft.attributes),
                )
            )
        return tuple(entities)

    def _materialize_edges(
        self,
        case_id: UUID,
        edges: dict[str, _EdgeDraft],
        key_to_canonical: dict[str, str],
    ) -> tuple[EntityEdge, ...]:
        results: list[EntityEdge] = []
        ordered = sorted(
            edges.values(),
            key=lambda item: (
                item.relationship_type.value,
                item.source_key,
                item.target_key,
            ),
        )
        for draft in ordered:
            source_id = key_to_canonical.get(draft.source_key)
            target_id = key_to_canonical.get(draft.target_key)
            if source_id is None or target_id is None:
                continue
            support_count = max(len(draft.evidence_ids), 1)
            confidence = boost_confidence(
                confidence_for_relationship(draft.relationship_type),
                support_count,
            )
            rel_id = relationship_key(
                source_id,
                target_id,
                draft.relationship_type.value,
            )
            results.append(
                EntityEdge(
                    relationship_id=rel_id,
                    case_id=case_id,
                    source_canonical_id=source_id,
                    target_canonical_id=target_id,
                    relationship_type=draft.relationship_type,
                    confidence=confidence,
                    explanation=draft.explanation,
                    support_count=support_count,
                    evidence_ids=tuple(sorted(draft.evidence_ids, key=str)),
                    supports=tuple(draft.supports),
                    provenance=build_edge_provenance(
                        case_id=case_id,
                        relationship_type=draft.relationship_type.value,
                        source_canonical_id=source_id,
                        target_canonical_id=target_id,
                        evidence_ids=[str(item) for item in draft.evidence_ids],
                        extraction_ids=list(draft.extraction_ids),
                        finding_ids=list(draft.finding_ids),
                        correlation_ids=list(draft.correlation_ids),
                        timeline_ids=list(draft.timeline_ids),
                        fusion_ids=list(draft.fusion_ids),
                    ),
                )
            )
        return tuple(results)
