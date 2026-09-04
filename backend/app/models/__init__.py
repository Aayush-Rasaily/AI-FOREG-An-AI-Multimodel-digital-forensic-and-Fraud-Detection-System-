"""SQLAlchemy persistence models."""

from backend.app.models.ai import AIModelRecord, InferenceJob, InferenceLog
from backend.app.models.audio_ai import (
    AudioAIFinding,
    AudioAIFindingRegion,
    AudioAnalysisRun,
)
from backend.app.models.audit import AuditEvent
from backend.app.models.case import Case
from backend.app.models.case_intelligence import (
    CaseConflictRecord,
    CaseEvidenceParticipationRecord,
    CaseIntelligenceRun,
    CaseRelationshipRecord,
    CaseTimelineEventRecord,
)
from backend.app.models.collaboration import (
    ActivityLog,
    CaseMember,
    CaseWorkflowState,
    EvidenceAssignment,
    InvestigationComment,
    InvestigationMention,
    InvestigationReview,
    InvestigationTask,
    Notification,
)
from backend.app.models.comparison import (
    ComparisonRun,
    Difference,
    DifferenceRegion,
    ReferenceEvidence,
)
from backend.app.models.correlation import (
    CorrelationAnalysisRun,
    CorrelationSupportRecord,
    EvidenceCorrelationRecord,
)
from backend.app.models.custody import ChainOfCustodyEvent
from backend.app.models.document_ai import (
    DocumentAIFinding,
    DocumentAIFindingRegion,
    DocumentAnalysisRun,
)
from backend.app.models.entity import (
    EntityRelationshipRecord,
    EntityResolutionRun,
    EntitySupportRecord,
    InvestigationEntityRecord,
)
from backend.app.models.evidence import Evidence
from backend.app.models.extraction import ExtractionRecord
from backend.app.models.forensic_report import ForensicReport
from backend.app.models.forensics import AnalysisRun, Finding, FindingRegion
from backend.app.models.fusion import (
    FusionAnalysisRun,
    FusionConflictRecord,
    JuryAssessmentRecord,
)
from backend.app.models.image_ai import (
    ImageAIFinding,
    ImageAIFindingRegion,
    ImageAnalysisRun,
)
from backend.app.models.investigation_summary import InvestigationSummary
from backend.app.models.monitoring import (
    AuditStatistics,
    MonitoringSnapshot,
    SystemHealthRecord,
)
from backend.app.models.permission import Permission
from backend.app.models.processing import Artifact, ProcessingJob
from backend.app.models.role import Role
from backend.app.models.session import RefreshToken, UserSession
from backend.app.models.signature_ai import SignatureVerificationRun
from backend.app.models.system import SystemDiagnosticsRun
from backend.app.models.timeline import (
    InvestigationTimeline,
    TimelineConflictRecord,
    TimelineEventRecord,
)
from backend.app.models.user import User
from backend.app.models.video_ai import (
    VideoAIFinding,
    VideoAIFindingRegion,
    VideoAnalysisRun,
)
from backend.app.models.workflow import (
    InvestigationWorkflow,
    WorkflowMilestone,
    WorkflowNote,
    WorkflowNotification,
    WorkflowReview,
    WorkflowTask,
)
from backend.app.models.security import (
    CaseAccessRecord,
    ComplianceReport,
    PolicyViolation,
    SecurityPermission,
    SecurityRole,
)
from backend.app.models.interoperability import (
    ExportJob,
    ImportJob,
    PackageManifestRecord,
)
from backend.app.models.knowledge_graph import (
    GraphEntity,
    GraphEntityAlias,
    GraphProvenance,
    GraphRelationship,
    KnowledgeGraphRun,
)
from backend.app.models.investigation_intelligence import (
    EvidenceGapRecordRow,
    InvestigationHypothesis,
    InvestigationIntelligenceRun,
    InvestigationRecommendation,
)

__all__ = [
    "AIModelRecord",
    "AnalysisRun",
    "AuditEvent",
    "AuditStatistics",
    "Artifact",
    "Case",
    "CaseConflictRecord",
    "CaseEvidenceParticipationRecord",
    "CaseIntelligenceRun",
    "CaseMember",
    "CaseRelationshipRecord",
    "CaseTimelineEventRecord",
    "CaseWorkflowState",
    "ChainOfCustodyEvent",
    "ActivityLog",
    "ComparisonRun",
    "CorrelationAnalysisRun",
    "CorrelationSupportRecord",
    "Difference",
    "DifferenceRegion",
    "DocumentAIFinding",
    "DocumentAIFindingRegion",
    "DocumentAnalysisRun",
    "EntityRelationshipRecord",
    "EntityResolutionRun",
    "EntitySupportRecord",
    "Evidence",
    "EvidenceAssignment",
    "EvidenceCorrelationRecord",
    "ExtractionRecord",
    "Finding",
    "FindingRegion",
    "ForensicReport",
    "FusionAnalysisRun",
    "FusionConflictRecord",
    "JuryAssessmentRecord",
    "MonitoringSnapshot",
    "ImageAIFinding",
    "ImageAIFindingRegion",
    "ImageAnalysisRun",
    "InferenceJob",
    "InferenceLog",
    "InvestigationComment",
    "InvestigationEntityRecord",
    "InvestigationMention",
    "InvestigationReview",
    "InvestigationSummary",
    "InvestigationTask",
    "InvestigationTimeline",
    "InvestigationWorkflow",
    "Notification",
    "Permission",
    "ProcessingJob",
    "ReferenceEvidence",
    "RefreshToken",
    "Role",
    "SignatureVerificationRun",
    "SystemDiagnosticsRun",
    "SystemHealthRecord",
    "TimelineConflictRecord",
    "TimelineEventRecord",
    "User",
    "UserSession",
    "VideoAIFinding",
    "VideoAIFindingRegion",
    "VideoAnalysisRun",
    "AudioAIFinding",
    "AudioAIFindingRegion",
    "AudioAnalysisRun",
    "WorkflowMilestone",
    "WorkflowNote",
    "WorkflowNotification",
    "WorkflowReview",
    "WorkflowTask",
    "CaseAccessRecord",
    "ComplianceReport",
    "PolicyViolation",
    "SecurityPermission",
    "SecurityRole",
    "ExportJob",
    "ImportJob",
    "PackageManifestRecord",
    "KnowledgeGraphRun",
    "GraphEntity",
    "GraphRelationship",
    "GraphEntityAlias",
    "GraphProvenance",
    "InvestigationIntelligenceRun",
    "InvestigationHypothesis",
    "EvidenceGapRecordRow",
    "InvestigationRecommendation",
]
