import {
  AlertTriangle,
  Download,
  FileBarChart,
  FileText,
  ShieldAlert,
  Sparkles,
} from "lucide-react";

import {
  useForensicReportLatestQuery,
  useGenerateForensicReportMutation,
} from "../../hooks/useForensicReport";
import { ApiClientError } from "../../services/api/client";
import { forensicReportService } from "../../services/api/forensicReport";
import type { ReportStatus } from "../../types/forensicReport";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

interface ForensicReportPanelProps {
  caseId: string;
}

const statusTone: Record<
  ReportStatus,
  "neutral" | "primary" | "success" | "warning" | "error"
> = {
  QUEUED: "neutral",
  GENERATING: "primary",
  COMPLETED: "success",
  FAILED: "error",
};

function formatPercent(value: number | null | undefined): string {
  if (value == null) return "—";
  return `${Math.round(value * 100)}%`;
}

export function ForensicReportPanel({ caseId }: ForensicReportPanelProps) {
  const latestQuery = useForensicReportLatestQuery(caseId);
  const generateMutation = useGenerateForensicReportMutation();

  const isLoading = latestQuery.isLoading;
  const isNotFound =
    latestQuery.error instanceof ApiClientError && latestQuery.error.status === 404;
  const report = latestQuery.data?.data;
  const sections = (report?.content?.sections ?? {}) as Record<string, unknown>;
  const executiveSummary = (report?.executive_summary ??
    sections.executive_summary ??
    {}) as Record<string, unknown>;
  const explainability = (report?.explainability ??
    sections.explainability ??
    {}) as Record<string, unknown>;
  const inventory = (sections.evidence_inventory ?? []) as Array<
    Record<string, unknown>
  >;
  const jury = (sections.multimodal_jury_assessment ?? []) as Array<
    Record<string, unknown>
  >;
  const conflicts = [
    ...((sections.conflicts_and_contradictions ?? []) as Array<
      Record<string, unknown>
    >),
    ...((explainability.conflicts ?? []) as Array<Record<string, unknown>>),
  ];
  const timeline = (sections.investigation_timeline ?? []) as Array<
    Record<string, unknown>
  >;
  const limitations = (sections.confidence_and_limitations ?? {}) as Record<
    string,
    unknown
  >;

  return (
    <Panel
      description="Professional forensic investigation report aggregating evidence, fusion, jury, and case intelligence."
      title="Forensic Investigation Report"
    >
      <div className="space-y-4 p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="space-y-1">
            {report && (
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone={statusTone[report.status]}>{report.status}</Badge>
                <span className="text-xs text-muted">
                  Version {report.report_version}
                </span>
                {report.completed_at && (
                  <span className="text-xs text-muted">
                    Generated {new Date(report.completed_at).toLocaleString()}
                  </span>
                )}
              </div>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            {report?.has_pdf && report.status === "COMPLETED" && (
              <a
                className="inline-flex h-8 items-center justify-center gap-2 rounded-lg border border-border-strong bg-background-offset px-3 text-xs font-medium text-foreground hover:bg-surface-muted"
                download
                href={forensicReportService.downloadUrl(report.id)}
              >
                <Download aria-hidden="true" size={14} />
                Download PDF
              </a>
            )}
            <Button
              disabled={generateMutation.isPending}
              onClick={() => generateMutation.mutate({ caseId })}
              size="sm"
              variant="secondary"
            >
              <Sparkles aria-hidden="true" className="mr-1.5" size={14} />
              {generateMutation.isPending ? "Queuing…" : "Generate Report"}
            </Button>
          </div>
        </div>

        {isLoading && <LoadingState label="Loading forensic report…" />}

        {!isLoading && latestQuery.isError && !isNotFound && (
          <ErrorState
            description="Unable to load forensic report."
            title="Report unavailable"
          />
        )}

        {!isLoading && (isNotFound || !report) && (
          <EmptyState
            description="Generate a forensic report to create a stable, auditable snapshot of this investigation."
            icon={<FileBarChart aria-hidden="true" size={20} />}
            title="No forensic report yet"
          />
        )}

        {report && report.status === "GENERATING" && (
          <LoadingState label="Generating forensic report…" />
        )}

        {report && report.status === "FAILED" && (
          <ErrorState
            description={
              report.error_message ?? "Report generation failed."
            }
            title="Report generation failed"
          />
        )}

        {report && report.status === "COMPLETED" && (
          <>
            <div className="grid gap-2 sm:grid-cols-4">
              <div className="rounded-lg border border-border bg-background/40 p-3">
                <p className="text-[10px] uppercase tracking-wide text-subtle">
                  Case Verdict
                </p>
                <p className="text-sm text-foreground">
                  {String(executiveSummary.case_verdict ?? "—").replaceAll(
                    "_",
                    " ",
                  )}
                </p>
              </div>
              <div className="rounded-lg border border-border bg-background/40 p-3">
                <p className="text-[10px] uppercase tracking-wide text-subtle">
                  Risk Score
                </p>
                <p className="text-sm text-foreground">
                  {executiveSummary.risk_score != null
                    ? String(executiveSummary.risk_score)
                    : "—"}
                </p>
              </div>
              <div className="rounded-lg border border-border bg-background/40 p-3">
                <p className="text-[10px] uppercase tracking-wide text-subtle">
                  Confidence
                </p>
                <p className="text-sm text-foreground">
                  {formatPercent(executiveSummary.confidence as number | null)}
                </p>
              </div>
              <div className="rounded-lg border border-border bg-background/40 p-3">
                <p className="text-[10px] uppercase tracking-wide text-subtle">
                  Evidence
                </p>
                <p className="text-sm text-foreground">
                  {report.evidence_count}
                </p>
              </div>
            </div>

            {Boolean(explainability.why) && (
              <p className="rounded-lg border border-border bg-background/40 p-3 text-xs text-muted">
                {String(explainability.why)}
              </p>
            )}

            {inventory.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-xs font-medium uppercase tracking-wide text-muted">
                  Evidence Overview
                </h3>
                <div className="space-y-2">
                  {inventory.map((item) => (
                    <div
                      className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border bg-background/50 p-3"
                      key={String(item.evidence_id)}
                    >
                      <div>
                        <p className="text-xs font-medium text-foreground">
                          {String(item.evidence_number)}
                        </p>
                        <p className="text-[11px] text-muted">
                          {String(item.filename)}
                        </p>
                      </div>
                      <Badge tone="neutral">
                        {String(item.coverage_status ?? "unknown").replaceAll(
                          "_",
                          " ",
                        )}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {jury.length > 0 && (
              <div className="space-y-2">
                <h3 className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-muted">
                  <FileText aria-hidden="true" size={14} />
                  AI Jury Assessment
                </h3>
                <p className="text-[11px] text-subtle">
                  {String(
                    explainability.jury_note ??
                      "AI/system-generated assessments, not live human expert opinions.",
                  )}
                </p>
                {jury.map((item) => (
                  <div
                    className="rounded-lg border border-border bg-background/40 p-3"
                    key={String(item.evidence_id)}
                  >
                    <p className="text-xs font-medium text-foreground">
                      {String(item.evidence_number)} —{" "}
                      {String(item.verdict ?? "—").replaceAll("_", " ")}
                    </p>
                  </div>
                ))}
              </div>
            )}

            {conflicts.length > 0 && (
              <div className="space-y-2">
                <h3 className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-warning">
                  <AlertTriangle aria-hidden="true" size={14} />
                  Conflicts
                </h3>
                {conflicts.map((conflict, index) => (
                  <div
                    className="rounded-lg border border-warning/40 bg-warning-soft p-3"
                    key={String(conflict.conflict_id ?? index)}
                  >
                    <p className="text-xs font-medium text-warning">
                      {String(conflict.conflict_type ?? "conflict").replaceAll(
                        "_",
                        " ",
                      )}
                    </p>
                    <p className="mt-1 text-[11px] text-warning/85">
                      {String(conflict.explanation ?? "")}
                    </p>
                  </div>
                ))}
              </div>
            )}

            {timeline.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-xs font-medium uppercase tracking-wide text-muted">
                  Timeline
                </h3>
                {timeline.slice(0, 5).map((event) => (
                  <div
                    className="rounded-lg border border-border bg-background/40 p-3"
                    key={String(event.event_id)}
                  >
                    <p className="text-xs text-muted">
                      {String(event.description)}
                    </p>
                  </div>
                ))}
              </div>
            )}

            {Array.isArray(limitations.limitations) &&
              limitations.limitations.length > 0 && (
                <div className="space-y-1">
                  <h3 className="text-xs font-medium uppercase tracking-wide text-muted">
                    Limitations
                  </h3>
                  {(limitations.limitations as string[]).map((item) => (
                    <p className="text-[11px] text-subtle" key={item}>
                      {item}
                    </p>
                  ))}
                </div>
              )}

            {report.provenance?.report_sha256 && (
              <p className="flex items-center gap-1.5 font-mono text-[10px] text-subtle">
                <ShieldAlert aria-hidden="true" size={12} />
                Report SHA-256: {String(report.provenance.report_sha256)}
              </p>
            )}
          </>
        )}
      </div>
    </Panel>
  );
}
