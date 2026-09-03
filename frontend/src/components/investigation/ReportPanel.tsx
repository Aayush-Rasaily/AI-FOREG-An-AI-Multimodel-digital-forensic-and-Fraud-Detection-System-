import { ChevronDown, ChevronRight, Download, FileBarChart } from "lucide-react";
import { useMemo, useState } from "react";

import {
  useGenerateReportMutation,
  useReportHistoryQuery,
  useReportLatestQuery,
} from "../../hooks/useReports";
import { ApiClientError } from "../../services/api/client";
import { reportsService } from "../../services/api/reports";
import type { ReportDownloadFormat, ReportStatus } from "../../types/reports";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

interface ReportPanelProps {
  caseId: string;
}

const statusTone: Record<ReportStatus, "neutral" | "cyan" | "green" | "amber" | "red"> =
  {
    QUEUED: "neutral",
    GENERATING: "cyan",
    COMPLETED: "green",
    FAILED: "red",
  };

const SECTION_LABELS: Record<string, string> = {
  case_summary: "Case Summary",
  evidence_inventory: "Evidence Inventory",
  metadata_summary: "Metadata Summary",
  ocr_summary: "OCR Summary",
  pattern_extraction_summary: "Pattern Extraction",
  timeline: "Timeline",
  forensic_findings: "Forensic Findings",
  evidence_comparison: "Evidence Comparison",
  image_ai: "Image AI",
  document_ai: "Document AI",
  signature_ai: "Signature AI",
  video_ai: "Video AI",
  audio_ai: "Audio AI",
  fusion_assessment: "Fusion Assessment",
  correlation_summary: "Correlation Summary",
  entity_graph_summary: "Entity Graph Summary",
  overall_confidence: "Overall Confidence",
  risk_assessment: "Risk Assessment",
  conflicts: "Conflicts",
  provenance_summary: "Provenance Summary",
  chain_of_custody_summary: "Chain of Custody",
  appendix_raw_findings: "Appendix",
};

export function ReportPanel({ caseId }: ReportPanelProps) {
  const latestQuery = useReportLatestQuery(caseId);
  const historyQuery = useReportHistoryQuery(caseId);
  const generateMutation = useGenerateReportMutation();
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  const isNotFound =
    latestQuery.error instanceof ApiClientError && latestQuery.error.status === 404;
  const report = latestQuery.data?.data;
  const isRunning =
    report?.status === "QUEUED" || report?.status === "GENERATING";
  const sections = (report?.content?.sections ?? {}) as Record<string, unknown>;
  const sectionOrder =
    report?.section_order?.length
      ? report.section_order
      : Object.keys(SECTION_LABELS);

  const history = historyQuery.data?.data.items ?? [];

  const previewKeys = useMemo(
    () => sectionOrder.filter((key) => key in SECTION_LABELS),
    [sectionOrder],
  );

  function download(format: ReportDownloadFormat) {
    if (!report) {
      return;
    }
    window.open(reportsService.downloadUrl(report.id, format), "_blank");
  }

  return (
    <Panel
      description="Deterministic investigation report compiled from Phases 1–7C outputs. No re-analysis is performed."
      title="Investigation Report"
    >
      <div className="space-y-4 p-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap gap-2">
            {report && (
              <>
                <Badge tone={statusTone[report.status]}>{report.status}</Badge>
                {report.report_checksum && (
                  <Badge tone="neutral">
                    checksum {report.report_checksum.slice(0, 12)}…
                  </Badge>
                )}
              </>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            {report?.status === "COMPLETED" && (
              <>
                <Button onClick={() => download("json")} size="sm" variant="secondary">
                  <Download size={14} /> JSON
                </Button>
                <Button onClick={() => download("md")} size="sm" variant="secondary">
                  <Download size={14} /> Markdown
                </Button>
                <Button onClick={() => download("html")} size="sm" variant="secondary">
                  <Download size={14} /> HTML
                </Button>
              </>
            )}
            <Button
              disabled={generateMutation.isPending || isRunning}
              onClick={() => generateMutation.mutate({ caseId })}
              size="sm"
              variant="secondary"
            >
              {generateMutation.isPending || isRunning
                ? "Generating…"
                : "Generate Report"}
            </Button>
          </div>
        </div>

        {(latestQuery.isLoading || isRunning) && (
          <LoadingState label="Loading investigation report…" />
        )}

        {!latestQuery.isLoading && latestQuery.isError && !isNotFound && (
          <ErrorState
            description="Unable to load investigation reports."
            title="Report unavailable"
          />
        )}

        {!latestQuery.isLoading &&
          !isRunning &&
          (isNotFound || !report) && (
            <EmptyState
              description="Generate a report to compile evidence, timeline, correlations, entities, and AI outputs."
              icon={<FileBarChart aria-hidden="true" size={19} />}
              title="No reports"
            />
          )}

        {report?.status === "COMPLETED" && (
          <div className="space-y-3">
            <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-3 text-xs text-slate-300">
              <p>Engine {report.engine_version} · Report {report.report_version}</p>
              <p className="mt-1">Evidence hashes: {report.evidence_count}</p>
              {report.report_checksum && (
                <p className="mt-1 break-all">Checksum: {report.report_checksum}</p>
              )}
              {report.completed_at && (
                <p className="mt-1">Generated: {report.completed_at}</p>
              )}
            </div>

            {previewKeys.map((key) => {
              const section = sections[key] as
                | Record<string, unknown>
                | undefined;
              const isOpen = expanded[key] ?? false;
              const count =
                typeof section?.count === "number"
                  ? section.count
                  : Array.isArray(section?.items)
                    ? section.items.length
                    : null;
              return (
                <div
                  className="rounded-lg border border-slate-800 bg-slate-950/40 p-3"
                  key={key}
                >
                  <button
                    className="flex w-full items-center gap-2 text-left text-sm text-slate-100"
                    onClick={() =>
                      setExpanded((current) => ({
                        ...current,
                        [key]: !isOpen,
                      }))
                    }
                    type="button"
                  >
                    {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                    <span>{SECTION_LABELS[key] ?? key}</span>
                    {count != null && (
                      <Badge tone="neutral">{count}</Badge>
                    )}
                    {section?.available === false && (
                      <Badge tone="amber">missing</Badge>
                    )}
                  </button>
                  {isOpen && (
                    <pre className="mt-2 overflow-x-auto rounded bg-slate-900 p-2 text-[11px] text-slate-400">
                      {JSON.stringify(section ?? { available: false }, null, 2)}
                    </pre>
                  )}
                </div>
              );
            })}

            {history.length > 1 && (
              <div className="rounded-lg border border-slate-800 p-3">
                <p className="mb-2 text-xs font-medium text-slate-200">
                  Previous reports
                </p>
                <ul className="space-y-1 text-xs text-slate-400">
                  {history.map((item) => (
                    <li key={item.id}>
                      {item.id.slice(0, 8)}… · {item.status} ·{" "}
                      {item.report_checksum?.slice(0, 10) ?? "no checksum"}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </Panel>
  );
}
