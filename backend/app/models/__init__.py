"""SQLAlchemy persistence models."""

from backend.app.models.ai import AIModelRecord, InferenceJob, InferenceLog
from backend.app.models.audio_ai import (
    AudioAIFinding,
    AudioAIFindingRegion,
    AudioAnalysisRun,
)
from backend.app.models.case import Case
from backend.app.models.comparison import (
    ComparisonRun,
    Difference,
    DifferenceRegion,
    ReferenceEvidence,
)
from backend.app.models.custody import ChainOfCustodyEvent
from backend.app.models.document_ai import (
    DocumentAIFinding,
    DocumentAIFindingRegion,
    DocumentAnalysisRun,
)
from backend.app.models.evidence import Evidence
from backend.app.models.extraction import ExtractionRecord
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
from backend.app.models.processing import Artifact, ProcessingJob
from backend.app.models.signature_ai import SignatureVerificationRun
from backend.app.models.video_ai import (
    VideoAIFinding,
    VideoAIFindingRegion,
    VideoAnalysisRun,
)

__all__ = [
    "AIModelRecord",
    "AnalysisRun",
    "Artifact",
    "Case",
    "ChainOfCustodyEvent",
    "ComparisonRun",
    "Difference",
    "DifferenceRegion",
    "DocumentAIFinding",
    "DocumentAIFindingRegion",
    "DocumentAnalysisRun",
    "Evidence",
    "ExtractionRecord",
    "Finding",
    "FindingRegion",
    "FusionAnalysisRun",
    "FusionConflictRecord",
    "JuryAssessmentRecord",
    "ImageAIFinding",
    "ImageAIFindingRegion",
    "ImageAnalysisRun",
    "InferenceJob",
    "InferenceLog",
    "ProcessingJob",
    "ReferenceEvidence",
    "SignatureVerificationRun",
    "VideoAIFinding",
    "VideoAIFindingRegion",
    "VideoAnalysisRun",
    "AudioAIFinding",
    "AudioAIFindingRegion",
    "AudioAnalysisRun",
]
