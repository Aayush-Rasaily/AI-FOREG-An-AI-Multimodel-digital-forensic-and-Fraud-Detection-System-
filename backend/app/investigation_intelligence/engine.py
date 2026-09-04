"""Investigation intelligence engine — collect, analyze, never re-run AI."""

from __future__ import annotations

from collections import defaultdict
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.investigation_intelligence.evidence_gaps import detect_gaps
from backend.app.investigation_intelligence.hypothesis import generate_hypotheses
from backend.app.investigation_intelligence.models import (
    CoverageMetrics,
    IntelligenceResult,
)
from backend.app.investigation_intelligence.policy import (
    II_ENGINE_VERSION,
    II_POLICY_VERSION,
)
from backend.app.investigation_intelligence.recommendations import (
    generate_recommendations,
)
from backend.app.investigation_intelligence.scoring import investigation_score
from backend.app.models.case import Case
from backend.app.models.correlation import EvidenceCorrelationRecord
from backend.app.models.custody import ChainOfCustodyEvent
from backend.app.models.document_ai import DocumentAIFinding
from backend.app.models.evidence import Evidence
from backend.app.models.extraction import ExtractionRecord
from backend.app.models.forensic_report import ForensicReport
from backend.app.models.fusion import FusionAnalysisRun, FusionConflictRecord
from backend.app.models.image_ai import ImageAIFinding
from backend.app.models.knowledge_graph import (
    GraphEntity,
    GraphRelationship,
    KnowledgeGraphRun,
)
from backend.app.models.signature_ai import SignatureVerificationRun
from backend.app.models.timeline import (
    InvestigationTimeline,
    TimelineConflictRecord,
    TimelineEventRecord,
)


class InvestigationIntelligenceEngine:
    """Rule-based deterministic investigation intelligence."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def load_case(self, case_id: UUID) -> Case | None:
        return await self.session.get(Case, case_id)

    async def analyze(self, case: Case) -> IntelligenceResult:
        snapshot = await self.collect(case.id)
        coverage = self.compute_coverage(snapshot)
        hypotheses = generate_hypotheses(snapshot, coverage)
        gaps = detect_gaps(snapshot, coverage)
        recommendations = generate_recommendations(hypotheses, gaps)
        high_gaps = sum(1 for gap in gaps if gap.severity.value == "HIGH")
        score = investigation_score(
            overall_completeness=coverage.overall_completeness,
            open_conflicts=coverage.open_conflicts,
            high_priority_gaps=high_gaps,
            hypothesis_count=len(hypotheses),
        )
        open_conflicts = list(snapshot.get("open_conflicts", []))
        return IntelligenceResult(
            hypotheses=hypotheses,
            gaps=gaps,
            recommendations=recommendations,
            coverage=coverage,
            investigation_score=score,
            open_conflicts=open_conflicts,
            provenance={
                "engine_version": II_ENGINE_VERSION,
                "policy_version": II_POLICY_VERSION,
                "evidence_count": len(snapshot.get("evidence", [])),
                "sources": sorted(snapshot.get("source_kinds", [])),
            },
        )

    async def collect(self, case_id: UUID) -> dict[str, Any]:
        evidence_rows = await self._evidence(case_id)
        evidence_ids = [UUID(row["id"]) for row in evidence_rows]
        extractions = await self._extractions(evidence_ids)
        ai_findings = await self._ai_findings(evidence_ids)
        signatures = await self._signatures(evidence_ids)
        correlations = await self._correlations(case_id)
        timeline_events, timeline_conflicts, clusters = await self._timeline(
            case_id
        )
        fusion_runs, fusion_conflicts = await self._fusion(evidence_ids)
        graph_entities, graph_relationships = await self._graph(case_id)
        custody = await self._custody(evidence_ids)
        reports = await self._reports(case_id)

        open_conflicts: list[dict[str, Any]] = []
        for item in timeline_conflicts:
            open_conflicts.append(
                {
                    "kind": "timeline",
                    "id": item["id"],
                    "detail": item.get("conflict_type"),
                }
            )
        for item in fusion_conflicts:
            open_conflicts.append(
                {
                    "kind": "fusion",
                    "id": item["id"],
                    "detail": item.get("conflict_type"),
                }
            )

        source_kinds = {"case", "evidence"}
        if extractions:
            source_kinds.add("extraction")
        if ai_findings:
            source_kinds.add("ai")
        if correlations:
            source_kinds.add("correlation")
        if timeline_events:
            source_kinds.add("timeline")
        if fusion_runs:
            source_kinds.add("fusion")
        if graph_entities:
            source_kinds.add("knowledge_graph")
        if reports:
            source_kinds.add("report")
        if any(custody.values()):
            source_kinds.add("custody")

        return {
            "evidence": evidence_rows,
            "extractions": extractions,
            "ai_findings": ai_findings,
            "signatures": signatures,
            "correlations": correlations,
            "timeline_events": timeline_events,
            "timeline_conflicts": timeline_conflicts,
            "timeline_event_clusters": clusters,
            "fusion_runs": fusion_runs,
            "fusion_conflicts": fusion_conflicts,
            "graph_entities": graph_entities,
            "graph_relationships": graph_relationships,
            "custody_by_evidence": custody,
            "reports": reports,
            "open_conflicts": open_conflicts,
            "source_kinds": list(source_kinds),
        }

    def compute_coverage(self, snapshot: dict[str, Any]) -> CoverageMetrics:
        evidence = snapshot.get("evidence", [])
        total = len(evidence)
        ai_ids = {str(item["evidence_id"]) for item in snapshot.get("ai_findings", [])}
        fusion_ids = {
            str(item["evidence_id"]) for item in snapshot.get("fusion_runs", [])
        }
        analyzed = len(ai_ids | fusion_ids)
        pending = max(0, total - analyzed)
        custody = snapshot.get("custody_by_evidence", {})
        with_custody = sum(1 for eid in custody if int(custody.get(eid, 0) or 0) > 0)
        with_meta = sum(1 for item in evidence if item.get("has_metadata"))
        with_ts = sum(1 for item in evidence if item.get("has_timestamp"))

        def ratio(num: int, den: int) -> float:
            if den <= 0:
                return 0.0
            return round(num / den, 4)

        timeline_cov = 1.0 if snapshot.get("timeline_events") else 0.0
        graph_cov = 1.0 if snapshot.get("graph_entities") else 0.0
        corr_cov = (
            1.0
            if snapshot.get("correlations")
            else (0.0 if total >= 2 else 1.0)
        )
        fusion_cov = ratio(len(fusion_ids), total) if total else 0.0
        ai_cov = ratio(len(ai_ids), total) if total else 0.0
        meta_cov = ratio(with_meta + with_ts, total * 2) if total else 0.0
        custody_cov = ratio(with_custody, total) if total else 0.0

        components = [
            ratio(analyzed, total) if total else 0.0,
            timeline_cov,
            graph_cov,
            corr_cov,
            fusion_cov,
            ai_cov,
            meta_cov,
            custody_cov,
        ]
        overall = round(sum(components) / len(components), 4) if total else 0.0

        return CoverageMetrics(
            evidence_total=total,
            evidence_analyzed=analyzed,
            evidence_pending=pending,
            timeline_coverage=timeline_cov,
            knowledge_graph_coverage=graph_cov,
            correlation_coverage=corr_cov,
            fusion_coverage=fusion_cov,
            ai_coverage=ai_cov,
            metadata_completeness=meta_cov,
            chain_of_custody_completeness=custody_cov,
            overall_completeness=overall,
            open_conflicts=len(snapshot.get("open_conflicts", [])),
        )

    async def _evidence(self, case_id: UUID) -> list[dict[str, Any]]:
        result = await self.session.execute(
            select(Evidence).where(Evidence.case_id == case_id)
        )
        rows = list(result.scalars().all())
        out: list[dict[str, Any]] = []
        for row in sorted(rows, key=lambda item: str(item.id)):
            meta = getattr(row, "metadata_json", None) or {}
            out.append(
                {
                    "id": str(row.id),
                    "mime_type": row.mime_type,
                    "sha256_hash": row.sha256_hash,
                    "original_filename": row.original_filename,
                    "has_metadata": bool(meta),
                    "has_timestamp": bool(
                        getattr(row, "created_at", None)
                        or getattr(row, "uploaded_at", None)
                    ),
                    "missing_original": not bool(
                        getattr(row, "storage_key", None)
                        or getattr(row, "stored_filename", None)
                    ),
                }
            )
        return out

    async def _extractions(
        self, evidence_ids: list[UUID],
    ) -> list[dict[str, Any]]:
        if not evidence_ids:
            return []
        result = await self.session.execute(
            select(ExtractionRecord).where(
                ExtractionRecord.evidence_id.in_(evidence_ids)
            )
        )
        rows = list(result.scalars().all())
        return [
            {"id": str(row.id), "evidence_id": str(row.evidence_id)}
            for row in sorted(rows, key=lambda item: str(item.id))
        ]

    async def _ai_findings(
        self, evidence_ids: list[UUID],
    ) -> list[dict[str, Any]]:
        if not evidence_ids:
            return []
        out: list[dict[str, Any]] = []
        img = await self.session.execute(
            select(ImageAIFinding).where(
                ImageAIFinding.evidence_id.in_(evidence_ids)
            )
        )
        for row in img.scalars().all():
            category = str(getattr(row, "category", "") or "")
            detector = str(getattr(row, "detector", "") or "")
            description = str(getattr(row, "description", "") or "")
            out.append(
                {
                    "id": str(row.id),
                    "evidence_id": str(row.evidence_id),
                    "finding_type": f"{category} {detector} {description}",
                    "confidence": float(getattr(row, "confidence", 0) or 0),
                    "modality": "image",
                }
            )
        doc = await self.session.execute(
            select(DocumentAIFinding).where(
                DocumentAIFinding.evidence_id.in_(evidence_ids)
            )
        )
        for doc_row in doc.scalars().all():
            category = str(getattr(doc_row, "category", "") or "")
            detector = str(getattr(doc_row, "detector", "") or "")
            description = str(getattr(doc_row, "description", "") or "")
            out.append(
                {
                    "id": str(doc_row.id),
                    "evidence_id": str(doc_row.evidence_id),
                    "finding_type": f"{category} {detector} {description}",
                    "confidence": float(getattr(doc_row, "confidence", 0) or 0),
                    "modality": "document",
                }
            )
        return sorted(out, key=lambda item: item["id"])

    async def _signatures(
        self, evidence_ids: list[UUID],
    ) -> list[dict[str, Any]]:
        if not evidence_ids:
            return []
        result = await self.session.execute(
            select(SignatureVerificationRun).where(
                SignatureVerificationRun.questioned_evidence_id.in_(
                    evidence_ids
                )
            )
        )
        rows = list(result.scalars().all())
        return [
            {
                "id": str(row.id),
                "evidence_id": (
                    str(row.questioned_evidence_id)
                    if row.questioned_evidence_id
                    else None
                ),
                "status": str(getattr(row, "verdict", "")),
                "consistent": str(getattr(row, "verdict", "")).upper()
                in {"MATCH", "VALID", "AUTHENTIC"},
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
        out: list[dict[str, Any]] = []
        for row in sorted(rows, key=lambda item: str(item.id)):
            left = getattr(row, "left_evidence_id", None) or getattr(
                row, "evidence_a_id", None
            )
            right = getattr(row, "right_evidence_id", None) or getattr(
                row, "evidence_b_id", None
            )
            out.append(
                {
                    "id": str(row.id),
                    "left_evidence_id": str(left) if left else None,
                    "right_evidence_id": str(right) if right else None,
                    "correlation_type": str(
                        getattr(row, "correlation_type", "") or ""
                    ),
                    "confidence": float(
                        getattr(row, "confidence", None)
                        or getattr(row, "score", None)
                        or 0
                    ),
                }
            )
        return out

    async def _timeline(
        self, case_id: UUID,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        tl = await self.session.execute(
            select(InvestigationTimeline)
            .where(InvestigationTimeline.case_id == case_id)
            .order_by(InvestigationTimeline.created_at.desc())
        )
        timeline = tl.scalars().first()
        if timeline is None:
            return [], [], []
        events_result = await self.session.execute(
            select(TimelineEventRecord).where(
                TimelineEventRecord.timeline_id == timeline.id
            )
        )
        events = list(events_result.scalars().all())
        event_rows = [
            {
                "id": str(row.id),
                "timeline_id": str(timeline.id),
                "evidence_id": str(row.evidence_id) if row.evidence_id else None,
                "event_type": str(getattr(row, "event_type", "")),
            }
            for row in sorted(events, key=lambda item: str(item.id))
        ]
        conflicts_result = await self.session.execute(
            select(TimelineConflictRecord).where(
                TimelineConflictRecord.timeline_id == timeline.id
            )
        )
        conflicts = [
            {
                "id": str(row.id),
                "conflict_type": str(getattr(row, "conflict_type", "")),
                "evidence_ids": (
                    [str(row.evidence_id)] if row.evidence_id else []
                ),
            }
            for row in sorted(
                conflicts_result.scalars().all(), key=lambda item: str(item.id)
            )
        ]
        clusters_map: dict[str, set[str]] = defaultdict(set)
        for row in event_rows:
            evidence_id = row["evidence_id"]
            event_id = row["id"]
            if evidence_id and event_id:
                clusters_map[str(event_id)].add(str(evidence_id))
        clusters = [
            {"event_id": event_id, "evidence_ids": sorted(eids)}
            for event_id, eids in sorted(clusters_map.items())
            if len(eids) >= 1
        ]
        return event_rows, conflicts, clusters

    async def _fusion(
        self, evidence_ids: list[UUID],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        if not evidence_ids:
            return [], []
        runs_result = await self.session.execute(
            select(FusionAnalysisRun).where(
                FusionAnalysisRun.evidence_id.in_(evidence_ids)
            )
        )
        runs = list(runs_result.scalars().all())
        run_rows = [
            {
                "id": str(row.id),
                "evidence_id": str(row.evidence_id),
                "verdict": str(row.verdict) if row.verdict else "",
                "risk_score": float(row.risk_score or 0),
                "confidence": float(row.confidence or 0),
            }
            for row in sorted(runs, key=lambda item: str(item.id))
        ]
        run_ids = [row.id for row in runs]
        conflicts: list[dict[str, Any]] = []
        if run_ids:
            conf_result = await self.session.execute(
                select(FusionConflictRecord).where(
                    FusionConflictRecord.analysis_run_id.in_(run_ids)
                )
            )
            conflicts = [
                {
                    "id": str(row.id),
                    "conflict_type": str(getattr(row, "conflict_type", "")),
                }
                for row in sorted(
                    conf_result.scalars().all(), key=lambda item: str(item.id)
                )
            ]
        return run_rows, conflicts

    async def _graph(
        self, case_id: UUID,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        run_result = await self.session.execute(
            select(KnowledgeGraphRun)
            .where(KnowledgeGraphRun.case_id == case_id)
            .order_by(KnowledgeGraphRun.created_at.desc())
        )
        run = run_result.scalars().first()
        if run is None:
            return [], []
        entities_result = await self.session.execute(
            select(GraphEntity).where(GraphEntity.graph_id == run.id)
        )
        entities = [
            {
                "id": str(row.id),
                "entity_key": row.entity_key,
                "entity_type": row.entity_type,
                "evidence_ids": list(row.evidence_ids_json or []),
            }
            for row in sorted(
                entities_result.scalars().all(), key=lambda item: item.entity_key
            )
        ]
        rels_result = await self.session.execute(
            select(GraphRelationship).where(GraphRelationship.graph_id == run.id)
        )
        rels = [
            {
                "id": str(row.id),
                "relationship_type": row.relationship_type,
                "source_entity_key": row.source_entity_key,
                "target_entity_key": row.target_entity_key,
                "evidence_ids": list(row.evidence_ids_json or []),
            }
            for row in sorted(
                rels_result.scalars().all(),
                key=lambda item: item.relationship_key,
            )
        ]
        return entities, rels

    async def _custody(
        self, evidence_ids: list[UUID],
    ) -> dict[str, int]:
        if not evidence_ids:
            return {}
        result = await self.session.execute(
            select(
                ChainOfCustodyEvent.evidence_id,
                func.count(ChainOfCustodyEvent.id),
            )
            .where(ChainOfCustodyEvent.evidence_id.in_(evidence_ids))
            .group_by(ChainOfCustodyEvent.evidence_id)
        )
        counts = {str(eid): int(count) for eid, count in result.all()}
        for eid in evidence_ids:
            counts.setdefault(str(eid), 0)
        return counts

    async def _reports(self, case_id: UUID) -> list[dict[str, Any]]:
        result = await self.session.execute(
            select(ForensicReport).where(ForensicReport.case_id == case_id)
        )
        rows = list(result.scalars().all())
        return [
            {"id": str(row.id)}
            for row in sorted(rows, key=lambda item: str(item.id))
        ]
