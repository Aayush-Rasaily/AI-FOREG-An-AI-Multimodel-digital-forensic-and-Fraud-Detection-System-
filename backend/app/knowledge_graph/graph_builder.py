"""Extract candidate entities from persisted investigation outputs."""

from __future__ import annotations

import re
from typing import Any
from uuid import UUID

from backend.app.knowledge_graph.entity_resolution import (
    make_identity_key,
    normalize_identity_value,
)
from backend.app.knowledge_graph.models import (
    CandidateEntity,
    GraphEntityType,
    GraphProvenanceRef,
)

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(?:\+?\d[\d\-\s().]{7,}\d)")
IP_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
)
DOMAIN_RE = re.compile(
    r"\b(?:[a-zA-Z0-9\-]+\.)+[a-zA-Z]{2,}\b"
)
URL_RE = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
HASH_RE = re.compile(r"\b[a-fA-F0-9]{64}\b")


def _prov(
    *,
    kind: str,
    source_id: str,
    evidence_id: str | None = None,
    finding_id: str | None = None,
    timeline_id: str | None = None,
    correlation_id: str | None = None,
    fusion_id: str | None = None,
    ocr_field: str | None = None,
    metadata_field: str | None = None,
    timestamp: str | None = None,
    detail: str | None = None,
) -> GraphProvenanceRef:
    return GraphProvenanceRef(
        source_kind=kind,
        source_id=source_id,
        evidence_id=evidence_id,
        finding_id=finding_id,
        timeline_id=timeline_id,
        correlation_id=correlation_id,
        fusion_id=fusion_id,
        ocr_field=ocr_field,
        metadata_field=metadata_field,
        timestamp=timestamp,
        detail=detail,
    )


def _candidate(
    entity_type: GraphEntityType,
    display: str,
    *,
    identity_kind: str,
    evidence_id: str | None = None,
    provenance: GraphProvenanceRef | None = None,
    attributes: dict[str, Any] | None = None,
) -> CandidateEntity:
    identity = make_identity_key(identity_kind, display)
    attrs = dict(attributes or {})
    attrs[f"identity:{identity_kind}"] = identity
    return CandidateEntity(
        entity_type=entity_type,
        display_name=display.strip() or normalize_identity_value(display),
        normalized_key=identity,
        identity_keys=(identity,),
        attributes=attrs,
        evidence_ids=(evidence_id,) if evidence_id else (),
        provenance=(provenance,) if provenance else (),
    )


def candidates_from_case(
    case_id: UUID,
    case_number: str,
    title: str,
) -> list[CandidateEntity]:
    return [
        _candidate(
            GraphEntityType.CASE,
            case_number or str(case_id),
            identity_kind="CASE",
            provenance=_prov(
                kind="case",
                source_id=str(case_id),
                detail=title,
            ),
            attributes={"case_id": str(case_id), "title": title},
        )
    ]


def candidates_from_evidence(rows: list[dict[str, Any]]) -> list[CandidateEntity]:
    out: list[CandidateEntity] = []
    for row in rows:
        eid = str(row["id"])
        filename = str(
            row.get("original_filename") or row.get("stored_filename") or eid
        )
        sha = str(row.get("sha256_hash") or "")
        mime = str(row.get("mime_type") or "")
        media_type = GraphEntityType.FILE
        if mime.startswith("image/"):
            media_type = GraphEntityType.IMAGE
        elif mime.startswith("video/"):
            media_type = GraphEntityType.VIDEO
        elif mime.startswith("audio/"):
            media_type = GraphEntityType.AUDIO
        elif "pdf" in mime or "document" in mime:
            media_type = GraphEntityType.DOCUMENT

        prov = _prov(kind="evidence", source_id=eid, evidence_id=eid)
        out.append(
            _candidate(
                GraphEntityType.EVIDENCE,
                filename,
                identity_kind="EVIDENCE",
                evidence_id=eid,
                provenance=prov,
                attributes={"evidence_id": eid, "mime_type": mime},
            )
        )
        file_identity = (
            make_identity_key("FILENAME_HASH", f"{filename}|{sha}")
            if sha
            else make_identity_key("FILE", filename)
        )
        file_candidate = CandidateEntity(
            entity_type=media_type,
            display_name=filename,
            normalized_key=file_identity,
            identity_keys=(file_identity,),
            attributes={
                "evidence_id": eid,
                "sha256": sha,
                "mime_type": mime,
                "identity:FILENAME_HASH": file_identity if sha else None,
            },
            evidence_ids=(eid,),
            provenance=(prov,),
        )
        out.append(file_candidate)
        if sha:
            out.append(
                _candidate(
                    GraphEntityType.HASH,
                    sha,
                    identity_kind="HASH",
                    evidence_id=eid,
                    provenance=prov,
                )
            )
    return out


def candidates_from_text(
    text: str,
    *,
    evidence_id: str | None,
    source_kind: str,
    source_id: str,
    ocr_field: str | None = None,
) -> list[CandidateEntity]:
    if not text:
        return []
    prov = _prov(
        kind=source_kind,
        source_id=source_id,
        evidence_id=evidence_id,
        ocr_field=ocr_field,
    )
    out: list[CandidateEntity] = []
    for match in sorted(set(EMAIL_RE.findall(text))):
        out.append(
            _candidate(
                GraphEntityType.EMAIL,
                match,
                identity_kind="EMAIL",
                evidence_id=evidence_id,
                provenance=prov,
            )
        )
    for match in sorted(set(PHONE_RE.findall(text))):
        digits = re.sub(r"\D", "", match)
        if len(digits) < 8:
            continue
        out.append(
            _candidate(
                GraphEntityType.PHONE,
                digits,
                identity_kind="PHONE",
                evidence_id=evidence_id,
                provenance=prov,
            )
        )
    for match in sorted(set(IP_RE.findall(text))):
        out.append(
            _candidate(
                GraphEntityType.IP_ADDRESS,
                match,
                identity_kind="IP_ADDRESS",
                evidence_id=evidence_id,
                provenance=prov,
            )
        )
    for match in sorted(set(URL_RE.findall(text))):
        out.append(
            _candidate(
                GraphEntityType.URL,
                match,
                identity_kind="URL",
                evidence_id=evidence_id,
                provenance=prov,
            )
        )
    for match in sorted(set(HASH_RE.findall(text))):
        out.append(
            _candidate(
                GraphEntityType.HASH,
                match.lower(),
                identity_kind="HASH",
                evidence_id=evidence_id,
                provenance=prov,
            )
        )
    # Domains excluding emails
    emails = {m.lower() for m in EMAIL_RE.findall(text)}
    for match in sorted(set(DOMAIN_RE.findall(text))):
        if any(match.lower() in email for email in emails):
            continue
        if match.lower().startswith("http"):
            continue
        out.append(
            _candidate(
                GraphEntityType.DOMAIN,
                match.lower(),
                identity_kind="DOMAIN",
                evidence_id=evidence_id,
                provenance=prov,
            )
        )
    return out


def candidates_from_extractions(
    rows: list[dict[str, Any]],
) -> list[CandidateEntity]:
    out: list[CandidateEntity] = []
    for row in rows:
        content = str(row.get("content") or "")
        eid = str(row.get("evidence_id") or "") or None
        out.extend(
            candidates_from_text(
                content,
                evidence_id=eid,
                source_kind="extraction",
                source_id=str(row.get("id")),
                ocr_field="content",
            )
        )
    return out


def candidates_from_ai_findings(
    rows: list[dict[str, Any]],
) -> list[CandidateEntity]:
    out: list[CandidateEntity] = []
    for row in rows:
        eid = str(row.get("evidence_id") or "") or None
        fid = str(row.get("id"))
        desc = str(row.get("description") or row.get("category") or fid)
        prov = _prov(
            kind="ai_finding",
            source_id=fid,
            evidence_id=eid,
            finding_id=fid,
        )
        out.append(
            _candidate(
                GraphEntityType.AI_FINDING,
                desc[:200],
                identity_kind="AI_FINDING",
                evidence_id=eid,
                provenance=prov,
                attributes={
                    "finding_id": fid,
                    "category": row.get("category"),
                    "confidence": row.get("confidence"),
                },
            )
        )
        out.extend(
            candidates_from_text(
                desc,
                evidence_id=eid,
                source_kind="ai_finding",
                source_id=fid,
            )
        )
    return out


def candidates_from_timeline(
    events: list[dict[str, Any]],
) -> list[CandidateEntity]:
    out: list[CandidateEntity] = []
    for event in events:
        eid = str(event.get("evidence_id") or "") or None
        tid = str(event.get("timeline_id") or event.get("id"))
        desc = str(event.get("description") or event.get("event_type") or tid)
        prov = _prov(
            kind="timeline",
            source_id=str(event.get("id")),
            evidence_id=eid,
            timeline_id=tid,
            timestamp=str(event.get("timestamp") or "") or None,
        )
        out.append(
            _candidate(
                GraphEntityType.TIMELINE_EVENT,
                desc[:200],
                identity_kind="TIMELINE_EVENT",
                evidence_id=eid,
                provenance=prov,
                attributes={"event_type": event.get("event_type")},
            )
        )
        out.extend(
            candidates_from_text(
                desc,
                evidence_id=eid,
                source_kind="timeline",
                source_id=str(event.get("id")),
            )
        )
    return out
