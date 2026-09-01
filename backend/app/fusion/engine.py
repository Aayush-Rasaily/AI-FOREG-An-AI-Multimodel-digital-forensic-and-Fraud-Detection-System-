"""Fusion analysis engine orchestration."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.domain.processing import EvidenceClassification
from backend.app.fusion.aggregator import collect_normalized_findings
from backend.app.fusion.models import FusionResult
from backend.app.fusion.policy import fuse_evidence
from backend.app.infrastructure.database.repositories.processing import (
    ArtifactRepository,
)
from backend.app.models.evidence import Evidence


class FusionEngine:
    """Orchestrate multimodal evidence fusion without re-running analyzers."""

    async def analyze(
        self,
        session: AsyncSession,
        evidence: Evidence,
    ) -> FusionResult:
        classification = await self._classification(session, evidence)
        findings, modality_statuses = await collect_normalized_findings(
            session,
            evidence,
            classification,
        )
        return fuse_evidence(
            evidence_id=evidence.id,
            source_hash=evidence.sha256_hash,
            findings=findings,
            modality_statuses=modality_statuses,
        )

    async def _classification(
        self,
        session: AsyncSession,
        evidence: Evidence,
    ) -> EvidenceClassification:
        raw = evidence.metadata_json.get("classification")
        if isinstance(raw, str):
            try:
                return EvidenceClassification(raw)
            except ValueError:
                pass
        from backend.app.domain.processing import ArtifactType

        artifact_repository = ArtifactRepository(session)
        artifacts, _ = await artifact_repository.list_for_evidence(
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
