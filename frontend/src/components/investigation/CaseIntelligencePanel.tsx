import {
  AlertTriangle,
  FileBarChart,
  Link2,
  ShieldAlert,
  Sparkles,
} from "lucide-react";

import {
  useAnalyzeCaseIntelligenceMutation,
  useCaseIntelligenceLatestQuery,
} from "../../hooks/useCaseIntelligence";
import { ApiClientError } from "../../services/api/client";
import type { CaseVerdict, EvidenceCoverageStatus } from "../../types/caseIntelligence";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

interface CaseIntelligencePanelProps {
  caseId: string;
}

const verdictTone: Record<
  CaseVerdict,
  "neutral" | "cyan" | "green" | "amber" | "red"
> = {
  genuine: "green",
  suspicious: "amber",
  potential_fraud: "red",
  inconclusive: "neutral",
  insufficient_evidence: "neutral",
  unavailable: "neutral",
};

const coverageTone: Record<
  EvidenceCoverageStatus,
  "neutral" | "cyan" | "green" | "amber" | "red"
> = {
  analyzed: "green",
  not_analyzed: "neutral",
  inconclusive: "amber",
  insufficient_evidence: "amber",
  unavailable: "neutral",
  failed: "red",
};

function formatVerdict(value: CaseVerdict | null | undefined): string {
  if (!value) return "—";
  return value.replaceAll("_", " ");
}

function formatPercent(value: number | null | undefined): string {
  if (value == null) return "—";
  return `${Math.round(value * 100)}%`;
}

export function CaseIntelligencePanel({ caseId }: CaseIntelligencePanelProps) {
  const latestQuery = useCaseIntelligenceLatestQuery(caseId);
  const analyzeMutation = useAnalyzeCaseIntelligenceMutation();

  const isLoading = latestQuery.isLoading;
  const isNotFound =
    latestQuery.error instanceof ApiClientError && latestQuery.error.status === 404;
  const assessment = latestQuery.data?.data;

  return (
    <Panel
      description="Case-level forensic synthesis aggregating Phase 6F fusion results across all evidence."
      title="Case Intelligence Report"
    >
      <div className="space-y-4 p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="space-y-1">
            {assessment && (
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone={verdictTone[assessment.verdict ?? "inconclusive"]}>
                  {formatVerdict(assessment.verdict)}
                </Badge>
                {assessment.risk_score != null && (
                  <span className="text-xs text-slate-400">
                    Case risk: {assessment.risk_score}
                  </span>
                )}
                {assessment.confidence != null && (
                  <span className="text-xs text-slate-400">
                    Confidence: {formatPercent(assessment.confidence)}
                  </span>
                )}
              </div>
            )}
          </div>
          <Button
            disabled={analyzeMutation.isPending}
            onClick={() => analyzeMutation.mutate({ caseId })}
            size="sm"
            variant="secondary"
          >
            <Sparkles aria-hidden="true" className="mr-1.5" size={14} />
            {analyzeMutation.isPending ? "Queuing…" : "Run Case Synthesis"}
          </Button>
        </div>

        {isLoading && <LoadingState label="Loading case intelligence…" />}

        {!isLoading && latestQuery.isError && !isNotFound && (
          <ErrorState
            description="Unable to load case intelligence assessment."
            title="Case intelligence unavailable"
          />
        )}

        {!isLoading && (isNotFound || !assessment) && (
          <EmptyState
            description="Run case synthesis to aggregate evidence-level fusion results."
            icon={<FileBarChart aria-hidden="true" size={20} />}
            title="No case intelligence analysis yet"
          />
        )}

        {assessment && (
          <>
            {assessment.explanation && (
              <p className="rounded-lg border border-slate-800 bg-slate-950/40 p-3 text-xs text-slate-400">
                {assessment.explanation}
              </p>
            )}

            <div className="grid gap-2 sm:grid-cols-4">
              <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-3">
                <p className="text-[10px] uppercase tracking-wide text-slate-600">
                  Total Evidence
                </p>
                <p className="text-sm text-slate-200">
                  {assessment.coverage.total_evidence}
                </p>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-3">
                <p className="text-[10px] uppercase tracking-wide text-slate-600">
                  Analyzed
                </p>
                <p className="text-sm text-slate-200">
                  {assessment.coverage.analyzed}
                </p>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-3">
                <p className="text-[10px] uppercase tracking-wide text-slate-600">
                  Not Analyzed
                </p>
                <p className="text-sm text-slate-200">
                  {assessment.coverage.not_analyzed}
                </p>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-3">
                <p className="text-[10px] uppercase tracking-wide text-slate-600">
                  Open Conflicts
                </p>
                <p className="text-sm text-slate-200">
                  {assessment.coverage.open_conflicts}
                </p>
              </div>
            </div>

            {assessment.participations.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-xs font-medium uppercase tracking-wide text-slate-500">
                  Evidence-Level Verdicts
                </h3>
                <div className="space-y-2">
                  {assessment.participations.map((item) => (
                    <div
                      className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-800 bg-slate-950/50 p-3"
                      key={item.evidence_id}
                    >
                      <div>
                        <p className="text-xs font-medium text-slate-200">
                          {item.evidence_number}
                        </p>
                        <p className="text-[11px] text-slate-500">
                          {item.evidence_type} · {item.coverage_status.replaceAll("_", " ")}
                        </p>
                      </div>
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge tone={coverageTone[item.coverage_status]}>
                          {item.coverage_status.replaceAll("_", " ")}
                        </Badge>
                        {item.fusion_verdict && (
                          <Badge tone={verdictTone[item.fusion_verdict]}>
                            {formatVerdict(item.fusion_verdict)}
                          </Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {assessment.relationships.length > 0 && (
              <div className="space-y-2">
                <h3 className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-slate-500">
                  <Link2 aria-hidden="true" size={14} />
                  Cross-Evidence Relationships
                </h3>
                <div className="space-y-2">
                  {assessment.relationships.map((relationship) => (
                    <div
                      className="rounded-lg border border-slate-800 bg-slate-950/40 p-3"
                      key={relationship.relationship_id}
                    >
                      <p className="text-xs font-medium text-slate-200">
                        {relationship.relationship_type.replaceAll("_", " ")}
                      </p>
                      <p className="mt-1 text-[11px] text-slate-500">
                        {relationship.supporting_reason}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {assessment.conflicts.length > 0 && (
              <div className="space-y-2">
                <h3 className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-amber-500">
                  <AlertTriangle aria-hidden="true" size={14} />
                  Case Conflicts
                </h3>
                <div className="space-y-2">
                  {assessment.conflicts.map((conflict) => (
                    <div
                      className="rounded-lg border border-amber-900/40 bg-amber-950/20 p-3"
                      key={conflict.conflict_id}
                    >
                      <p className="text-xs font-medium text-amber-200">
                        {conflict.conflict_type.replaceAll("_", " ")}
                      </p>
                      <p className="mt-1 text-[11px] text-amber-100/80">
                        {conflict.explanation}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {assessment.limitations && (
              <p className="text-[11px] text-slate-600">{assessment.limitations}</p>
            )}

            {assessment.provenance?.case_id && (
              <p className="flex items-center gap-1.5 font-mono text-[10px] text-slate-600">
                <ShieldAlert aria-hidden="true" size={12} />
                Provenance case: {String(assessment.provenance.case_id)}
              </p>
            )}
          </>
        )}
      </div>
    </Panel>
  );
}
