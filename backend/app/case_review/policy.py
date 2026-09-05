"""Deterministic policy for Phase 9E case review."""

from __future__ import annotations

CR_ENGINE_VERSION = "9e.1.0"
CR_POLICY_VERSION = "1.0"

# Required approval roles (all must approve for APPROVED stage).
REQUIRED_APPROVER_ROLES: tuple[str, ...] = (
    "TECHNICAL_REVIEWER",
    "FORENSIC_REVIEWER",
    "LEAD_INVESTIGATOR",
    "CASE_SUPERVISOR",
)

CHECKLIST_ITEMS: tuple[tuple[str, str], ...] = (
    ("EVIDENCE_INTEGRITY", "Evidence Integrity"),
    ("SHA256_VERIFIED", "SHA256 Verified"),
    ("METADATA_VERIFIED", "Metadata Verified"),
    ("CHAIN_OF_CUSTODY_COMPLETE", "Chain of Custody Complete"),
    ("TIMELINE_REVIEWED", "Timeline Reviewed"),
    ("AI_FINDINGS_REVIEWED", "AI Findings Reviewed"),
    ("FUSION_REVIEWED", "Fusion Reviewed"),
    ("CORRELATIONS_REVIEWED", "Correlations Reviewed"),
    ("KNOWLEDGE_GRAPH_REVIEWED", "Knowledge Graph Reviewed"),
    ("HYPOTHESES_REVIEWED", "Hypotheses Reviewed"),
    ("RECOMMENDATIONS_REVIEWED", "Recommendations Reviewed"),
    ("REPORT_REVIEWED", "Report Reviewed"),
    ("FINAL_VALIDATION", "Final Validation"),
)

# Auto-pass confidence when supporting signals exist (never auto-approve).
AUTO_PASS_HINTS: dict[str, float] = {
    "EVIDENCE_INTEGRITY": 0.7,
    "SHA256_VERIFIED": 0.95,
    "METADATA_VERIFIED": 0.8,
    "CHAIN_OF_CUSTODY_COMPLETE": 0.85,
    "TIMELINE_REVIEWED": 0.75,
    "AI_FINDINGS_REVIEWED": 0.7,
    "FUSION_REVIEWED": 0.7,
    "CORRELATIONS_REVIEWED": 0.7,
    "KNOWLEDGE_GRAPH_REVIEWED": 0.65,
    "HYPOTHESES_REVIEWED": 0.65,
    "RECOMMENDATIONS_REVIEWED": 0.65,
    "REPORT_REVIEWED": 0.7,
    "FINAL_VALIDATION": 0.5,
}
