import { useState } from "react";
import { BrainCircuit } from "lucide-react";

import {
  useAnalyzeInvestigationIntelligenceMutation,
  useInvestigationIntelligenceQuery,
} from "../../hooks/useInvestigationIntelligenceEngine";
import { ApiClientError } from "../../services/api/client";
import { CoveragePanel } from "./CoveragePanel";
import { EvidenceGapPanel } from "./EvidenceGapPanel";
import { HypothesisPanel } from "./HypothesisPanel";
import { RecommendationsPanel } from "./RecommendationsPanel";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { Input } from "../ui/Input";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";
import { Select } from "../ui/Select";

interface InvestigationIntelligencePanelProps {
  caseId: string;
}

export function InvestigationIntelligencePanel({
  caseId,
}: InvestigationIntelligencePanelProps) {
  const query = useInvestigationIntelligenceQuery(caseId);
  const analyzeMutation = useAnalyzeInvestigationIntelligenceMutation(caseId);
  const [search, setSearch] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("all");

  const isNotFound =
    query.error instanceof ApiClientError && query.error.status === 404;
  const run = query.data?.data;

  return (
    <div className="space-y-4">
      <Panel
        description="Deterministic hypotheses, evidence gaps, and recommended actions from existing investigation outputs — without re-running AI models."
        title="Case Intelligence"
      >
        <div className="space-y-4 p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex flex-wrap gap-2">
              {run ? (
                <>
                  <Badge tone="cyan">{run.status}</Badge>
                  <Badge tone="neutral">
                    Score {run.investigation_score.toFixed(1)}
                  </Badge>
                  <Badge tone="neutral">
                    {(run.overall_completeness * 100).toFixed(0)}% complete
                  </Badge>
                  <Badge tone="neutral">
                    {run.hypothesis_count} hypotheses
                  </Badge>
                </>
              ) : (
                <Badge tone="neutral">Not analyzed</Badge>
              )}
            </div>
            <Button
              disabled={analyzeMutation.isPending}
              onClick={() => analyzeMutation.mutate()}
              size="sm"
            >
              <BrainCircuit size={14} /> Analyze case
            </Button>
          </div>

          <div className="flex flex-wrap items-end gap-3">
            <label className="block text-xs text-slate-400">
              Search
              <Input
                className="mt-1 w-56"
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Hypothesis, gap, or action"
                value={search}
              />
            </label>
            <label className="block text-xs text-slate-400">
              Priority
              <Select
                className="mt-1 w-40"
                onChange={(event) => setPriorityFilter(event.target.value)}
                value={priorityFilter}
              >
                <option value="all">All</option>
                <option value="HIGH">High</option>
                <option value="MEDIUM">Medium</option>
                <option value="LOW">Low</option>
              </Select>
            </label>
          </div>

          {query.isLoading ? (
            <LoadingState label="Loading case intelligence" />
          ) : null}
          {query.isError && !isNotFound ? (
            <ErrorState
              description="Unable to load investigation intelligence."
              title="Intelligence unavailable"
            />
          ) : null}
          {analyzeMutation.isError ? (
            <ErrorState
              description="Case intelligence analysis failed."
              title="Analysis error"
            />
          ) : null}
          {(isNotFound || (!run && !query.isLoading)) &&
          !analyzeMutation.isPending ? (
            <EmptyState
              description="Run analysis to generate hypotheses, gaps, and recommendations."
              title="No case intelligence"
            />
          ) : null}

          {run?.open_conflicts?.length ? (
            <div className="rounded-lg border border-amber-900/40 p-3 text-xs text-amber-200/80">
              Open conflicts: {run.open_conflicts.length}
            </div>
          ) : null}

          {run?.provenance ? (
            <div className="text-[11px] text-slate-600">
              Provenance · engine {String(run.engine_version)} · policy{" "}
              {String(run.policy_version)}
            </div>
          ) : null}
        </div>
      </Panel>

      <div className="grid gap-4 xl:grid-cols-2">
        <CoveragePanel
          coverage={run?.coverage ?? null}
          investigationScore={run?.investigation_score ?? null}
        />
        <HypothesisPanel
          hypotheses={run?.hypotheses ?? []}
          priorityFilter={priorityFilter}
          search={search}
        />
        <EvidenceGapPanel gaps={run?.gaps ?? []} search={search} />
        <RecommendationsPanel
          recommendations={run?.recommendations ?? []}
          search={search}
        />
      </div>
    </div>
  );
}
