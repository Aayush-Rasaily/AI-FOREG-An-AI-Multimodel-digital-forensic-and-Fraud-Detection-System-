import {
  useGenerateInvestigationSummaryMutation,
  useInvestigationSummaryLatestQuery,
} from "../../hooks/useInvestigationIntelligence";
import type { CaseRiskLevel } from "../../types/intelligence";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

interface InvestigationSummaryPanelProps {
  caseId: string;
}

const riskTone: Record<
  CaseRiskLevel,
  "success" | "warning" | "error" | "neutral"
> = {
  low: "success",
  medium: "warning",
  high: "error",
  critical: "error",
};

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object"
    ? (value as Record<string, unknown>)
    : {};
}

export function InvestigationSummaryPanel({
  caseId,
}: InvestigationSummaryPanelProps) {
  const latestQuery = useInvestigationSummaryLatestQuery(caseId);
  const generateMutation = useGenerateInvestigationSummaryMutation(caseId);
  const summary = latestQuery.data?.data;

  if (latestQuery.isLoading) {
    return <LoadingState label="Loading investigation summary" />;
  }

  if (latestQuery.isError) {
    return (
      <ErrorState
        description="Investigation summary could not be loaded."
        onRetry={() => void latestQuery.refetch()}
        title="Summary error"
      />
    );
  }

  if (!summary) {
    return (
      <Panel
        description="Synthesize stored analyses into an explainable case narrative."
        title="Investigation summary"
      >
        <div className="p-4">
          <EmptyState
            action={
              <Button
                disabled={generateMutation.isPending}
                onClick={() => void generateMutation.mutateAsync()}
              >
                Generate summary
              </Button>
            }
            description="No investigation intelligence summary has been generated for this case yet."
            title="No summary yet"
          />
        </div>
      </Panel>
    );
  }

  const overview = asRecord(summary.overview);
  const timeline = asRecord(summary.timeline_summary);
  const correlation = asRecord(summary.correlation_summary);
  const ai = asRecord(summary.ai_summary);
  const risk = String(summary.overall_risk) as CaseRiskLevel;
  const narrative = summary.narrative ?? [];

  return (
    <div className="space-y-4">
      <Panel
        description="Deterministic narrative built only from persisted forensic outputs."
        title="Investigation summary"
      >
        <div className="space-y-4 p-4">
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <Badge tone={riskTone[risk] ?? "neutral"}>
              Risk: {summary.overall_risk}
            </Badge>
            <Badge tone="primary">
              Confidence: {summary.overall_confidence}/100
            </Badge>
            <Button
              disabled={generateMutation.isPending}
              onClick={() => void generateMutation.mutateAsync()}
              size="sm"
              variant="secondary"
            >
              Regenerate
            </Button>
            <span className="text-muted">
              Generated {new Date(summary.generated_at).toLocaleString()}
            </span>
            <span className="text-subtle">
              engine {summary.engine_version}
            </span>
          </div>

          <section>
            <h3 className="mb-2 text-sm font-medium text-foreground">
              Case overview
            </h3>
            <p className="text-xs text-muted">
              Evidence: {String(overview.evidence_count ?? 0)} · Analyzed:{" "}
              {String(overview.analyzed_count ?? 0)} · Not analyzed:{" "}
              {String(overview.not_analyzed_count ?? 0)}
            </p>
          </section>

          <section className="space-y-2">
            <h3 className="text-sm font-medium text-foreground">Narrative</h3>
            {narrative.map((paragraph) => (
              <p
                className="rounded-lg border border-border px-3 py-2 text-xs leading-relaxed text-muted"
                key={`${paragraph.section}-${paragraph.text.slice(0, 24)}`}
              >
                <span className="mb-1 block text-[10px] uppercase tracking-wide text-muted">
                  {paragraph.section.replaceAll("_", " ")}
                </span>
                {paragraph.text}
              </p>
            ))}
          </section>

          <div className="grid gap-4 md:grid-cols-2">
            <section>
              <h3 className="mb-2 text-sm font-medium text-foreground">
                Timeline
              </h3>
              <p className="text-xs text-muted">
                {timeline.available
                  ? `Events: ${String(timeline.event_count ?? 0)}`
                  : "No timeline available."}
              </p>
            </section>
            <section>
              <h3 className="mb-2 text-sm font-medium text-foreground">
                Correlations
              </h3>
              <p className="text-xs text-muted">
                {correlation.available
                  ? `Correlations: ${String(correlation.correlation_count ?? 0)}`
                  : "No correlations available."}
              </p>
            </section>
            <section>
              <h3 className="mb-2 text-sm font-medium text-foreground">
                AI summary
              </h3>
              <p className="text-xs text-muted">
                Fusion runs:{" "}
                {String(asRecord(ai.fusion).run_count ?? 0)} · Agreement:{" "}
                {String(asRecord(ai.fusion).agreement ?? "n/a")}
              </p>
            </section>
            <section>
              <h3 className="mb-2 text-sm font-medium text-foreground">
                Evidence coverage
              </h3>
              <p className="text-xs text-muted">
                Types:{" "}
                {Object.keys(asRecord(overview.mime_types)).join(", ") || "n/a"}
              </p>
            </section>
          </div>
        </div>
      </Panel>

      <Panel
        description="Explainable next steps tied to stored findings."
        title="Recommendations"
      >
        <ul className="space-y-2 p-4">
          {summary.recommendations.map((item) => (
            <li
              className="rounded-lg border border-border px-3 py-2 text-xs"
              key={item.code}
            >
              <p className="font-medium text-foreground">{item.title}</p>
              <p className="mt-1 text-muted">{item.rationale}</p>
            </li>
          ))}
        </ul>
      </Panel>
    </div>
  );
}
