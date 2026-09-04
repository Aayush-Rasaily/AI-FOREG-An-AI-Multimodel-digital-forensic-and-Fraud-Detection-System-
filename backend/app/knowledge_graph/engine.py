"""Knowledge graph construction engine."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.knowledge_graph.entity_resolution import resolve_entities
from backend.app.knowledge_graph.graph_builder import (
    candidates_from_ai_findings,
    candidates_from_case,
    candidates_from_evidence,
    candidates_from_extractions,
    candidates_from_timeline,
)
from backend.app.knowledge_graph.models import (
    GraphProvenanceRef,
    KnowledgeGraphResult,
)
from backend.app.knowledge_graph.policy import KG_ENGINE_VERSION, KG_POLICY_VERSION
from backend.app.knowledge_graph.relationships import build_relationships
from backend.app.models.case import Case
from backend.app.models.correlation import EvidenceCorrelationRecord
from backend.app.models.evidence import Evidence
from backend.app.models.extraction import ExtractionRecord
from backend.app.models.timeline import InvestigationTimeline, TimelineEventRecord


class KnowledgeGraphEngine:
    """Assemble a deterministic knowledge graph from existing outputs."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def load_case(self, case_id: UUID) -> Case | None:
        return await self.session.get(Case, case_id)

    async def build(self, case: Case) -> KnowledgeGraphResult:
        evidence_rows = await self._evidence(case.id)
        evidence_ids = [row["id"] for row in evidence_rows]
        extractions = await self._extractions(evidence_ids)
        findings = await self._ai_findings(evidence_ids)
        timeline_events = await self._timeline_events(case.id)
        correlations = await self._correlations(case.id)

        candidates = []
        candidates.extend(
            candidates_from_case(case.id, case.case_number, case.title)
        )
        candidates.extend(candidates_from_evidence(evidence_rows))
        candidates.extend(candidates_from_extractions(extractions))
        candidates.extend(candidates_from_ai_findings(findings))
        candidates.extend(candidates_from_timeline(timeline_events))

        entities = resolve_entities(candidates)

        # Map evidence_id → entity_ids for structural edges
        evidence_entity: dict[str, str] = {}
        case_entity_id = None
        for entity in entities:
            if entity.entity_type.value == "CASE":
                case_entity_id = entity.entity_id
            if entity.entity_type.value == "EVIDENCE":
                eid = str(entity.attributes.get("evidence_id") or "")
                if eid:
                    evidence_entity[eid] = entity.entity_id

        part_of_pairs: list[tuple[str, str, GraphProvenanceRef]] = []
        mention_pairs: list[tuple[str, str, GraphProvenanceRef]] = []
        derived_pairs: list[tuple[str, str, GraphProvenanceRef]] = []
        correlation_pairs: list[
            tuple[str, str, str, float, GraphProvenanceRef]
        ] = []

        if case_entity_id:
            for eid, entity_id in sorted(evidence_entity.items()):
                part_of_pairs.append(
                    (
                        entity_id,
                        case_entity_id,
                        GraphProvenanceRef(
                            source_kind="case",
                            source_id=str(case.id),
                            evidence_id=eid,
                            detail="Evidence belongs to case.",
                        ),
                    )
                )

        # Evidence PART_OF links for FILE/IMAGE/etc. derived from same evidence
        for entity in entities:
            eid = str(entity.attributes.get("evidence_id") or "")
            if not eid or eid not in evidence_entity:
                continue
            if entity.entity_type.value == "EVIDENCE":
                continue
            if entity.entity_type.value in {
                "FILE",
                "IMAGE",
                "VIDEO",
                "AUDIO",
                "DOCUMENT",
                "HASH",
            }:
                derived_pairs.append(
                    (
                        entity.entity_id,
                        evidence_entity[eid],
                        GraphProvenanceRef(
                            source_kind="evidence",
                            source_id=eid,
                            evidence_id=eid,
                            detail="Media/hash derived from evidence.",
                        ),
                    )
                )

        # Mentions: entities that share evidence_id with an evidence node
        for entity in entities:
            if entity.entity_type.value in {"CASE", "EVIDENCE"}:
                continue
            for eid in entity.evidence_ids:
                if eid in evidence_entity:
                    mention_pairs.append(
                        (
                            evidence_entity[eid],
                            entity.entity_id,
                            GraphProvenanceRef(
                                source_kind="extraction",
                                source_id=entity.entity_id,
                                evidence_id=eid,
                                detail="Identifier observed on evidence.",
                            ),
                        )
                    )

        for item in correlations:
            left = evidence_entity.get(item["left_evidence_id"])
            right = evidence_entity.get(item["right_evidence_id"])
            if not left or not right:
                continue
            correlation_pairs.append(
                (
                    left,
                    right,
                    str(item.get("correlation_type") or "correlated"),
                    float(item.get("confidence") or item.get("score") or 0.8),
                    GraphProvenanceRef(
                        source_kind="correlation",
                        source_id=item["id"],
                        evidence_id=item["left_evidence_id"],
                        correlation_id=item["id"],
                    ),
                )
            )

        relationships = build_relationships(
            entities,
            correlation_pairs=correlation_pairs,
            mention_pairs=mention_pairs,
            part_of_pairs=part_of_pairs,
            derived_pairs=derived_pairs,
        )

        return KnowledgeGraphResult(
            case_id=case.id,
            entities=entities,
            relationships=relationships,
            provenance_summary={
                "evidence_count": len(evidence_rows),
                "extraction_count": len(extractions),
                "ai_finding_count": len(findings),
                "timeline_event_count": len(timeline_events),
                "correlation_count": len(correlations),
                "engine_version": KG_ENGINE_VERSION,
                "policy_version": KG_POLICY_VERSION,
            },
            metadata={
                "entity_count": len(entities),
                "relationship_count": len(relationships),
            },
        )

    async def _evidence(self, case_id: UUID) -> list[dict[str, Any]]:
        result = await self.session.execute(
            select(Evidence).where(Evidence.case_id == case_id)
        )
        rows = list(result.scalars().all())
        return [
            {
                "id": str(row.id),
                "original_filename": row.original_filename,
                "stored_filename": row.stored_filename,
                "mime_type": row.mime_type,
                "sha256_hash": row.sha256_hash,
            }
            for row in sorted(rows, key=lambda item: str(item.id))
        ]

    async def _extractions(self, evidence_ids: list[str]) -> list[dict[str, Any]]:
        if not evidence_ids:
            return []
        ids = [UUID(item) for item in evidence_ids]
        result = await self.session.execute(
            select(ExtractionRecord).where(ExtractionRecord.evidence_id.in_(ids))
        )
        rows = list(result.scalars().all())
        return [
            {
                "id": str(row.id),
                "evidence_id": str(row.evidence_id),
                "content": row.content,
            }
            for row in sorted(rows, key=lambda item: str(item.id))
        ]

    async def _ai_findings(self, evidence_ids: list[str]) -> list[dict[str, Any]]:
        """Collect AI findings from modality tables without re-running models."""

        if not evidence_ids:
            return []
        ids = [UUID(item) for item in evidence_ids]
        findings: list[dict[str, Any]] = []

        try:
            from backend.app.models.image_ai import ImageAIFinding

            result = await self.session.execute(
                select(ImageAIFinding).where(ImageAIFinding.evidence_id.in_(ids))
            )
            for row in result.scalars().all():
                findings.append(
                    {
                        "id": str(row.id),
                        "evidence_id": str(row.evidence_id),
                        "description": getattr(row, "description", None)
                        or getattr(row, "category", None)
                        or str(row.id),
                        "category": getattr(row, "category", None),
                        "confidence": getattr(row, "confidence", None),
                    }
                )
        except Exception:  # noqa: BLE001
            pass

        try:
            from backend.app.models.document_ai import DocumentAIFinding

            result = await self.session.execute(
                select(DocumentAIFinding).where(
                    DocumentAIFinding.evidence_id.in_(ids)
                )
            )
            for row in result.scalars().all():
                findings.append(
                    {
                        "id": str(row.id),
                        "evidence_id": str(row.evidence_id),
                        "description": getattr(row, "description", None)
                        or str(row.id),
                        "category": getattr(row, "category", None),
                        "confidence": getattr(row, "confidence", None),
                    }
                )
        except Exception:  # noqa: BLE001
            pass

        return sorted(findings, key=lambda item: item["id"])

    async def _timeline_events(self, case_id: UUID) -> list[dict[str, Any]]:
        result = await self.session.execute(
            select(InvestigationTimeline)
            .where(InvestigationTimeline.case_id == case_id)
            .order_by(InvestigationTimeline.created_at.desc())
        )
        timeline = result.scalars().first()
        if timeline is None:
            return []
        events_result = await self.session.execute(
            select(TimelineEventRecord).where(
                TimelineEventRecord.timeline_id == timeline.id
            )
        )
        rows = list(events_result.scalars().all())
        return [
            {
                "id": str(row.id),
                "timeline_id": str(timeline.id),
                "evidence_id": str(row.evidence_id) if row.evidence_id else None,
                "event_type": str(getattr(row, "event_type", "")),
                "description": getattr(row, "description", None),
                "timestamp": (
                    ts.isoformat()
                    if (ts := getattr(row, "timestamp", None)) is not None
                    and hasattr(ts, "isoformat")
                    else None
                ),
            }
            for row in sorted(rows, key=lambda item: str(item.id))
        ]

    async def _correlations(self, case_id: UUID) -> list[dict[str, Any]]:
        result = await self.session.execute(
            select(EvidenceCorrelationRecord).where(
                EvidenceCorrelationRecord.case_id == case_id
            )
        )
        rows = list(result.scalars().all())
        return [
            {
                "id": str(row.id),
                "left_evidence_id": str(row.left_evidence_id),
                "right_evidence_id": str(row.right_evidence_id),
                "correlation_type": str(getattr(row, "correlation_type", "")),
                "confidence": getattr(row, "confidence", None),
                "score": getattr(row, "score", None),
            }
            for row in sorted(rows, key=lambda item: str(item.id))
        ]
