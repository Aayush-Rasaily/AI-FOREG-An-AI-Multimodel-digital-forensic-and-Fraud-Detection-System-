import { lazy, Suspense, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft,
  Clock3,
  FileBarChart,
  Shield,
} from "lucide-react";

import { AiJuryPanel } from "../components/investigation/AiJuryPanel";
import { TimelinePanel } from "../components/investigation/TimelinePanel";
import { EvidenceCorrelationPanel } from "../components/investigation/EvidenceCorrelationPanel";
import { AuditTrailPanel } from "../components/investigation/AuditTrailPanel";
import { ReportPanel } from "../components/investigation/ReportPanel";
import { AnalysisPanel } from "../components/investigation/AnalysisPanel";
import { ComparisonPanel } from "../components/investigation/ComparisonPanel";
import { DocumentAnalysisPanel } from "../components/investigation/DocumentAnalysisPanel";
import { DifferencesPanel } from "../components/investigation/DifferencesPanel";
import { EvidenceList } from "../components/evidence/EvidenceList";
import { EvidenceUploadForm } from "../components/evidence/EvidenceUploadForm";
import { FindingsPanel } from "../components/investigation/FindingsPanel";
import { ImageAnalysisPanel } from "../components/investigation/ImageAnalysisPanel";
import { MetadataPanel } from "../components/investigation/MetadataPanel";
import { SignatureVerificationPanel } from "../components/investigation/SignatureVerificationPanel";
import { VideoAnalysisPanel } from "../components/investigation/VideoAnalysisPanel";
import { AudioAnalysisPanel } from "../components/investigation/AudioAnalysisPanel";
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
import { EvidenceViewer } from "../components/evidence/EvidenceViewer";

const EntityGraphPanel = lazy(() =>
  import("../components/investigation/EntityGraphPanel").then((module) => ({
    default: module.EntityGraphPanel,
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
  { value: "jury", label: "AI Jury" },
  { value: "metadata", label: "Metadata" },
  { value: "report", label: "Report" },
  { value: "audit", label: "Audit Trail" },
];

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
        {activeTab === "entities" && (
          <Suspense fallback={<LoadingState label="Loading entity graph…" />}>
            <EntityGraphPanel caseId={caseId} />
          </Suspense>
        )}
        {activeTab === "report" && <ReportPanel caseId={caseId} />}
        {activeTab === "audit" && <AuditTrailPanel caseId={caseId} />}
      </div>

      <div className="mt-5 flex items-center gap-2 text-[11px] text-slate-600">
        <Shield aria-hidden="true" size={13} />
        Chain-of-custody controls will be enforced by the backend integration.
      </div>
    </div>
  );
}

