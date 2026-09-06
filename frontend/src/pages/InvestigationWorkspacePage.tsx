import { lazy, Suspense, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft,
  Clock3,
  FileBarChart,
  Shield,
} from "lucide-react";

import { EvidenceList } from "../components/evidence/EvidenceList";
import { EvidenceUploadForm } from "../components/evidence/EvidenceUploadForm";
import { EvidenceViewer } from "../components/evidence/EvidenceViewer";
import { AnalysisPanel } from "../components/investigation/AnalysisPanel";
import { ComparisonPanel } from "../components/investigation/ComparisonPanel";
import { FindingsPanel } from "../components/investigation/FindingsPanel";
import { MetadataPanel } from "../components/investigation/MetadataPanel";
import { PageHeader } from "../components/layout/PageHeader";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { ErrorState } from "../components/ui/ErrorState";
import { LoadingState } from "../components/ui/LoadingState";
import { NotFoundState } from "../components/ui/NotFoundState";
import { Panel } from "../components/ui/Panel";
import { Tabs, type TabOption } from "../components/ui/Tabs";
import { useCaseQuery } from "../hooks/useCases";
import { useCaseEvidenceQuery } from "../hooks/useEvidence";
import { ApiClientError } from "../services/api/client";
import type { InvestigationTab } from "../types/investigation";

const AiJuryPanel = lazy(() =>
  import("../components/investigation/AiJuryPanel").then((m) => ({
    default: m.AiJuryPanel,
  })),
);
const TimelinePanel = lazy(() =>
  import("../components/investigation/TimelinePanel").then((m) => ({
    default: m.TimelinePanel,
  })),
);
const EvidenceCorrelationPanel = lazy(() =>
  import("../components/investigation/EvidenceCorrelationPanel").then((m) => ({
    default: m.EvidenceCorrelationPanel,
  })),
);
const AuditTrailPanel = lazy(() =>
  import("../components/investigation/AuditTrailPanel").then((m) => ({
    default: m.AuditTrailPanel,
  })),
);
const EntityGraphPanel = lazy(() =>
  import("../components/investigation/EntityGraphPanel").then((m) => ({
    default: m.EntityGraphPanel,
  })),
);
const DifferencesPanel = lazy(() =>
  import("../components/investigation/DifferencesPanel").then((m) => ({
    default: m.DifferencesPanel,
  })),
);
const ImageAnalysisPanel = lazy(() =>
  import("../components/investigation/ImageAnalysisPanel").then((m) => ({
    default: m.ImageAnalysisPanel,
  })),
);
const DocumentAnalysisPanel = lazy(() =>
  import("../components/investigation/DocumentAnalysisPanel").then((m) => ({
    default: m.DocumentAnalysisPanel,
  })),
);
const SignatureVerificationPanel = lazy(() =>
  import("../components/investigation/SignatureVerificationPanel").then((m) => ({
    default: m.SignatureVerificationPanel,
  })),
);
const VideoAnalysisPanel = lazy(() =>
  import("../components/investigation/VideoAnalysisPanel").then((m) => ({
    default: m.VideoAnalysisPanel,
  })),
);
const AudioAnalysisPanel = lazy(() =>
  import("../components/investigation/AudioAnalysisPanel").then((m) => ({
    default: m.AudioAnalysisPanel,
  })),
);
const ReportPanel = lazy(() =>
  import("../components/investigation/ReportPanel").then((m) => ({
    default: m.ReportPanel,
  })),
);
const InvestigationSummaryPanel = lazy(() =>
  import("../components/investigation/InvestigationSummaryPanel").then((m) => ({
    default: m.InvestigationSummaryPanel,
  })),
);
const KnowledgeGraphPanel = lazy(() =>
  import("../components/knowledge-graph/KnowledgeGraphPanel").then((m) => ({
    default: m.KnowledgeGraphPanel,
  })),
);
const InvestigationIntelligencePanel = lazy(() =>
  import("../components/investigation-intelligence/InvestigationIntelligencePanel").then(
    (m) => ({ default: m.InvestigationIntelligencePanel }),
  ),
);
const WorkflowDashboard = lazy(() =>
  import("../components/decision-support/WorkflowDashboard").then((m) => ({
    default: m.WorkflowDashboard,
  })),
);
const CaseReviewPanel = lazy(() =>
  import("../components/case-review/CaseReviewPanel").then((m) => ({
    default: m.CaseReviewPanel,
  })),
);
const IntegrityDashboard = lazy(() =>
  import("../components/integrity/IntegrityDashboard").then((m) => ({
    default: m.IntegrityDashboard,
  })),
);
const ActivityPanel = lazy(() =>
  import("../components/collaboration/ActivityPanel").then((m) => ({
    default: m.ActivityPanel,
  })),
);
const AssignmentsPanel = lazy(() =>
  import("../components/collaboration/AssignmentsPanel").then((m) => ({
    default: m.AssignmentsPanel,
  })),
);
const CaseMembersPanel = lazy(() =>
  import("../components/collaboration/CaseMembersPanel").then((m) => ({
    default: m.CaseMembersPanel,
  })),
);
const CommentsPanel = lazy(() =>
  import("../components/collaboration/CommentsPanel").then((m) => ({
    default: m.CommentsPanel,
  })),
);
const NotificationPanel = lazy(() =>
  import("../components/collaboration/NotificationPanel").then((m) => ({
    default: m.NotificationPanel,
  })),
);
const ReviewPanel = lazy(() =>
  import("../components/collaboration/ReviewPanel").then((m) => ({
    default: m.ReviewPanel,
  })),
);
const TaskBoard = lazy(() =>
  import("../components/collaboration/TaskBoard").then((m) => ({
    default: m.TaskBoard,
  })),
);
const WorkflowPanel = lazy(() =>
  import("../components/collaboration/WorkflowPanel").then((m) => ({
    default: m.WorkflowPanel,
  })),
);
const MilestoneTimeline = lazy(() =>
  import("../components/workflow/MilestoneTimeline").then((m) => ({
    default: m.MilestoneTimeline,
  })),
);
const InvestigationNotesPanel = lazy(() =>
  import("../components/workflow/NotesPanel").then((m) => ({
    default: m.NotesPanel,
  })),
);
const WorkflowNotificationsPanel = lazy(() =>
  import("../components/workflow/NotificationsPanel").then((m) => ({
    default: m.NotificationsPanel,
  })),
);
const InvestigationReviewPanel = lazy(() =>
  import("../components/workflow/ReviewPanel").then((m) => ({
    default: m.ReviewPanel,
  })),
);
const InvestigationTaskBoard = lazy(() =>
  import("../components/workflow/TaskBoard").then((m) => ({
    default: m.TaskBoard,
  })),
);
const InvestigationWorkflowPanel = lazy(() =>
  import("../components/workflow/WorkflowPanel").then((m) => ({
    default: m.WorkflowPanel,
  })),
);
const CaseAccessPanel = lazy(() =>
  import("../components/security/CaseAccessPanel").then((m) => ({
    default: m.CaseAccessPanel,
  })),
);
const CompliancePanel = lazy(() =>
  import("../components/security/CompliancePanel").then((m) => ({
    default: m.CompliancePanel,
  })),
);
const PolicyViolationsPanel = lazy(() =>
  import("../components/security/PolicyViolationsPanel").then((m) => ({
    default: m.PolicyViolationsPanel,
  })),
);
const CaseInteropSection = lazy(() =>
  import("./InteroperabilityPage").then((m) => ({
    default: m.CaseInteropSection,
  })),
);

const tabs: TabOption<InvestigationTab>[] = [
  { value: "overview", label: "Overview" },
  { value: "evidence", label: "Evidence" },
  { value: "forensics", label: "Forensics" },
  { value: "comparison", label: "Comparison" },
  { value: "findings", label: "Findings" },
  { value: "timeline", label: "Timeline" },
  { value: "correlations", label: "Correlations" },
  { value: "entities", label: "Entity Graph" },
  { value: "knowledge-graph", label: "Knowledge Graph" },
  { value: "case-intelligence", label: "Case Intelligence" },
  { value: "decision-support", label: "Decision Support" },
  { value: "case-review", label: "Case Review" },
  { value: "integrity", label: "Integrity" },
  { value: "jury", label: "AI Jury" },
  { value: "metadata", label: "Metadata" },
  { value: "report", label: "Report" },
  { value: "summary", label: "Summary" },
  { value: "collaboration", label: "Collaboration" },
  { value: "workflow", label: "Workflow" },
  { value: "security", label: "Security" },
  { value: "exchange", label: "Exchange" },
  { value: "audit", label: "Audit Trail" },
];

function TabFallback({ label }: { label: string }) {
  return <LoadingState label={label} />;
}

export function InvestigationWorkspacePage() {
  const { caseId } = useParams<{ caseId: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<InvestigationTab>("overview");
  const caseQuery = useCaseQuery(caseId);
  const evidenceQuery = useCaseEvidenceQuery(caseId);

  if (caseQuery.isPending) {
    return <LoadingState label="Loading case workspace" />;
  }
  if (caseQuery.isError) {
    return (
      <ErrorState
        description={
          caseQuery.error instanceof ApiClientError
            ? caseQuery.error.message
            : "The case workspace could not be loaded."
        }
        onRetry={() => void caseQuery.refetch()}
      />
    );
  }
  const caseRecord = caseQuery.data?.data;
  if (!caseRecord || !caseId) {
    return <NotFoundState />;
  }
  const evidence = evidenceQuery.data?.data.items ?? [];
  const primaryEvidence = evidence[0];

  return (
    <div>
      <PageHeader
        actions={
          <Button onClick={() => navigate("/reports")} variant="secondary">
            <FileBarChart aria-hidden="true" size={16} />
            Reports
          </Button>
        }
        description={caseRecord.description || "Preserve original evidence and review its custody history."}
        eyebrow="Investigation workspace"
        title={caseRecord.title}
      />

      <div className="mb-5 flex flex-wrap items-center gap-3 border-y border-slate-800 py-3">
        <Link
          className="inline-flex items-center gap-2 text-xs text-slate-500 hover:text-cyan-300"
          to="/investigations"
        >
          <ArrowLeft aria-hidden="true" size={14} />
          All investigations
        </Link>
        <span className="hidden h-4 w-px bg-slate-800 sm:block" />
        <Badge tone="neutral">Case ID: {caseRecord.case_number}</Badge>
        <Badge tone="cyan">{caseRecord.status.replaceAll("_", " ")}</Badge>
        <Badge tone="neutral">{evidenceQuery.data?.data.total ?? 0} evidence items</Badge>
        <span className="flex items-center gap-1.5 text-[11px] text-slate-600">
          <Clock3 aria-hidden="true" size={13} />
          Last activity unavailable
        </span>
      </div>

      <Tabs options={tabs} onChange={setActiveTab} value={activeTab} />

      <div className="mt-5">
        {activeTab === "overview" && (
          <div className="space-y-4">
            <div className="grid gap-4 xl:grid-cols-[0.9fr_1.6fr_1fr]">
              <Panel title="Evidence navigator">
                {evidenceQuery.isPending && <LoadingState label="Loading evidence" />}
                {evidenceQuery.isError && (
                  <ErrorState
                    description="Evidence records could not be loaded."
                    onRetry={() => void evidenceQuery.refetch()}
                  />
                )}
                {evidenceQuery.isSuccess && <EvidenceList items={evidence} />}
              </Panel>
              <EvidenceViewer />
              <div className="space-y-4">
                <AnalysisPanel evidence={primaryEvidence} />
                <ComparisonPanel evidence={primaryEvidence} />
                <FindingsPanel evidence={primaryEvidence} />
              </div>
            </div>
            <EvidenceUploadForm caseId={caseId} />
            <div className="grid gap-4 xl:grid-cols-2">
              <MetadataPanel />
            </div>
          </div>
        )}
        {activeTab === "evidence" && (
          <div className="space-y-4">
            <Panel title="Registered evidence">
              {evidenceQuery.isPending && <LoadingState label="Loading evidence" />}
              {evidenceQuery.isError && (
                <ErrorState
                  description="Evidence records could not be loaded."
                  onRetry={() => void evidenceQuery.refetch()}
                />
              )}
              {evidenceQuery.isSuccess && <EvidenceList items={evidence} />}
            </Panel>
            <EvidenceUploadForm caseId={caseId} />
          </div>
        )}
        <Suspense fallback={<TabFallback label="Loading panel…" />}>
          {activeTab === "jury" && <AiJuryPanel evidence={primaryEvidence} />}
          {activeTab === "findings" && <FindingsPanel evidence={primaryEvidence} />}
          {activeTab === "metadata" && <MetadataPanel />}
          {activeTab === "comparison" && (
            <div className="grid gap-4 xl:grid-cols-2">
              <ComparisonPanel evidence={primaryEvidence} />
              <DifferencesPanel evidence={primaryEvidence} />
            </div>
          )}
          {activeTab === "forensics" && (
            <div className="grid gap-4 xl:grid-cols-2">
              <AnalysisPanel evidence={primaryEvidence} />
              <ImageAnalysisPanel evidence={primaryEvidence} />
              <DocumentAnalysisPanel evidence={primaryEvidence} />
              <SignatureVerificationPanel
                evidence={primaryEvidence}
                referenceOptions={evidence}
              />
              <VideoAnalysisPanel evidence={primaryEvidence} />
              <AudioAnalysisPanel
                evidence={primaryEvidence}
                referenceOptions={evidence}
              />
              <FindingsPanel evidence={primaryEvidence} />
            </div>
          )}
          {activeTab === "timeline" && <TimelinePanel caseId={caseId} />}
          {activeTab === "correlations" && (
            <EvidenceCorrelationPanel caseId={caseId} />
          )}
          {activeTab === "entities" && <EntityGraphPanel caseId={caseId} />}
          {activeTab === "knowledge-graph" && (
            <KnowledgeGraphPanel caseId={caseId} />
          )}
          {activeTab === "case-intelligence" && (
            <InvestigationIntelligencePanel caseId={caseId} />
          )}
          {activeTab === "decision-support" && (
            <WorkflowDashboard caseId={caseId} />
          )}
          {activeTab === "case-review" && <CaseReviewPanel caseId={caseId} />}
          {activeTab === "integrity" && <IntegrityDashboard caseId={caseId} />}
          {activeTab === "report" && <ReportPanel caseId={caseId} />}
          {activeTab === "summary" && (
            <InvestigationSummaryPanel caseId={caseId} />
          )}
          {activeTab === "collaboration" && (
            <div className="space-y-4">
              <WorkflowPanel caseId={caseId} />
              <div className="grid gap-4 xl:grid-cols-2">
                <CaseMembersPanel caseId={caseId} />
                <NotificationPanel />
              </div>
              <div className="grid gap-4 xl:grid-cols-2">
                <TaskBoard caseId={caseId} />
                <AssignmentsPanel caseId={caseId} />
              </div>
              <div className="grid gap-4 xl:grid-cols-2">
                <CommentsPanel caseId={caseId} />
                <ReviewPanel caseId={caseId} />
              </div>
              <ActivityPanel caseId={caseId} />
            </div>
          )}
          {activeTab === "workflow" && (
            <div className="space-y-4">
              <InvestigationWorkflowPanel caseId={caseId} />
              <div className="grid gap-4 xl:grid-cols-2">
                <InvestigationTaskBoard caseId={caseId} />
                <InvestigationReviewPanel caseId={caseId} />
              </div>
              <div className="grid gap-4 xl:grid-cols-2">
                <MilestoneTimeline caseId={caseId} />
                <WorkflowNotificationsPanel caseId={caseId} />
              </div>
              <InvestigationNotesPanel caseId={caseId} />
            </div>
          )}
          {activeTab === "security" && (
            <div className="space-y-4">
              <div className="grid gap-4 xl:grid-cols-2">
                <CaseAccessPanel caseId={caseId} />
                <CompliancePanel caseId={caseId} />
              </div>
              <PolicyViolationsPanel caseId={caseId} />
            </div>
          )}
          {activeTab === "exchange" && <CaseInteropSection caseId={caseId} />}
          {activeTab === "audit" && <AuditTrailPanel caseId={caseId} />}
        </Suspense>
      </div>

      <div className="mt-5 flex items-center gap-2 text-[11px] text-slate-600">
        <Shield aria-hidden="true" size={13} />
        Chain-of-custody controls will be enforced by the backend integration.
      </div>
    </div>
  );
}
