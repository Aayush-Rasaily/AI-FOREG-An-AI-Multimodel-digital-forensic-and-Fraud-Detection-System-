"""Normalize findings from all modality sources."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from backend.app.ai.document.signature.schemas import SignatureVerdict
from backend.app.forensics.models import Severity
from backend.app.fusion.models import (
    FindingVerdict,
    Modality,
    ModalityAvailability,
    NormalizedFinding,
)

_CAPABILITY_CATEGORIES = frozenset(
    {
        "CAPABILITY",
        "SYNTHETIC_AUDIO",
        "SYNTHETIC_VIDEO",
        "VOICE_CLONE",
        "DEEPFAKE_VOICE",
        "DEEPFAKE",
    }
)


def _severity_from_value(raw: str | Severity) -> Severity:
    if isinstance(raw, Severity):
        return raw
    try:
        return Severity(str(raw))
    except ValueError:
        return Severity.INFO


def _verdict_from_finding(
    *,
    category: str,
    severity: Severity,
    confidence: float | None,
    metadata: dict[str, Any],
) -> FindingVerdict:
    status = metadata.get("status")
    if status == "unavailable" or category in _CAPABILITY_CATEGORIES:
        if metadata.get("reason") or status == "unavailable":
            return FindingVerdict.UNAVAILABLE
    if severity in {Severity.HIGH, Severity.CRITICAL}:
        if confidence is not None and confidence >= 0.7:
            return FindingVerdict.SUPPORTS_FRAUD
        return FindingVerdict.SUPPORTS_SUSPICIOUS
    if severity == Severity.MEDIUM:
        return FindingVerdict.SUPPORTS_SUSPICIOUS
    if severity == Severity.LOW:
        return FindingVerdict.INCONCLUSIVE
    return FindingVerdict.NEUTRAL


def _stable_finding_id(modality: Modality, source_id: str, detector: str) -> str:
    return f"{modality.value}:{source_id}:{detector}"


def normalize_forensic_finding(
    *,
    evidence_id: UUID,
    finding_id: UUID,
    detector: str,
    category: str,
    severity: Severity | str,
    confidence: float | None,
    description: str,
    explanation: str,
    metadata: dict[str, Any] | None = None,
) -> NormalizedFinding:
    meta = metadata or {}
    sev = _severity_from_value(severity)
    return NormalizedFinding(
        finding_id=_stable_finding_id(Modality.FORENSICS, str(finding_id), detector),
        evidence_id=evidence_id,
        modality=Modality.FORENSICS,
        analyzer="forensic_engine",
        category=category,
        finding_type=detector,
        verdict=_verdict_from_finding(
            category=category,
            severity=sev,
            confidence=confidence,
            metadata=meta,
        ),
        confidence=confidence,
        severity=sev,
        description=description,
        explanation=explanation,
        source_reference=f"forensics:{finding_id}",
        availability=ModalityAvailability.AVAILABLE,
        metadata=meta,
    )


def normalize_ai_finding(
    *,
    modality: Modality,
    evidence_id: UUID,
    finding_id: UUID,
    detector: str,
    category: str,
    severity: Severity | str,
    confidence: float | None,
    description: str,
    explanation: str,
    model_name: str = "",
    model_version: str = "",
    temporal: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> NormalizedFinding:
    meta = metadata or {}
    sev = _severity_from_value(severity)
    availability = ModalityAvailability.AVAILABLE
    verdict = _verdict_from_finding(
        category=category,
        severity=sev,
        confidence=confidence,
        metadata=meta,
    )
    if verdict == FindingVerdict.UNAVAILABLE:
        availability = ModalityAvailability.UNAVAILABLE
    return NormalizedFinding(
        finding_id=_stable_finding_id(modality, str(finding_id), detector),
        evidence_id=evidence_id,
        modality=modality,
        analyzer=detector,
        category=category,
        finding_type=detector,
        verdict=verdict,
        confidence=confidence,
        severity=sev,
        description=description,
        explanation=explanation,
        source_reference=f"{modality.value}:{finding_id}",
        availability=availability,
        model_name=model_name,
        model_version=model_version,
        temporal=temporal,
        metadata=meta,
    )


def normalize_comparison_difference(
    *,
    evidence_id: UUID,
    difference_id: UUID,
    matcher: str,
    difference_type: str,
    severity: Severity | str,
    confidence: float | None,
    description: str,
    explanation: str,
    metadata: dict[str, Any] | None = None,
) -> NormalizedFinding:
    meta = metadata or {}
    sev = _severity_from_value(severity)
    return NormalizedFinding(
        finding_id=_stable_finding_id(
            Modality.COMPARISON,
            str(difference_id),
            matcher,
        ),
        evidence_id=evidence_id,
        modality=Modality.COMPARISON,
        analyzer=matcher,
        category=difference_type,
        finding_type=difference_type,
        verdict=_verdict_from_finding(
            category=difference_type,
            severity=sev,
            confidence=confidence,
            metadata=meta,
        ),
        confidence=confidence,
        severity=sev,
        description=description,
        explanation=explanation,
        source_reference=f"comparison:{difference_id}",
        availability=ModalityAvailability.AVAILABLE,
        metadata=meta,
    )


def normalize_signature_verdict(
    *,
    evidence_id: UUID,
    run_id: UUID,
    verdict: SignatureVerdict,
    similarity: float | None,
    model_name: str,
    model_version: str,
    metadata: dict[str, Any] | None = None,
) -> NormalizedFinding:
    meta = metadata or {}
    if verdict == SignatureVerdict.UNAVAILABLE:
        finding_verdict = FindingVerdict.UNAVAILABLE
        availability = ModalityAvailability.UNAVAILABLE
        severity = Severity.INFO
    elif verdict == SignatureVerdict.NON_MATCH:
        finding_verdict = FindingVerdict.SUPPORTS_FRAUD
        availability = ModalityAvailability.AVAILABLE
        severity = Severity.HIGH
    elif verdict == SignatureVerdict.MATCH:
        finding_verdict = FindingVerdict.SUPPORTS_GENUINE
        availability = ModalityAvailability.AVAILABLE
        severity = Severity.INFO
    else:
        finding_verdict = FindingVerdict.INCONCLUSIVE
        availability = ModalityAvailability.AVAILABLE
        severity = Severity.LOW
    return NormalizedFinding(
        finding_id=_stable_finding_id(
            Modality.SIGNATURE_AI,
            str(run_id),
            "signature_verification",
        ),
        evidence_id=evidence_id,
        modality=Modality.SIGNATURE_AI,
        analyzer="signature_verification",
        category="SIGNATURE",
        finding_type="signature_verification",
        verdict=finding_verdict,
        confidence=similarity,
        severity=severity,
        description=f"Signature verification verdict: {verdict.value}",
        explanation=meta.get("explanation", f"Verdict {verdict.value}."),
        source_reference=f"signature:{run_id}",
        availability=availability,
        model_name=model_name,
        model_version=model_version,
        metadata=meta,
    )


def deduplicate_findings(
    findings: tuple[NormalizedFinding, ...],
) -> tuple[NormalizedFinding, ...]:
    """Remove duplicate normalized findings deterministically."""

    seen: set[str] = set()
    unique: list[NormalizedFinding] = []
    for finding in sorted(findings, key=lambda item: item.finding_id):
        if finding.finding_id in seen:
            continue
        seen.add(finding.finding_id)
        unique.append(finding)
    return tuple(unique)
