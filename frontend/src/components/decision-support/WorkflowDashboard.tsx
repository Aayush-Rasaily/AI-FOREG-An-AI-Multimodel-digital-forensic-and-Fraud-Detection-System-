import { useState } from "react";
import { ListTodo } from "lucide-react";

import {
  useCreateDecisionMutation,
  useDecisionSupportDecisionsQuery,
  useDecisionSupportQuery,
  useGenerateDecisionSupportMutation,
  useUpdateWorkflowTaskMutation,
} from "../../hooks/useDecisionSupport";
import { ApiClientError } from "../../services/api/client";
import { DecisionLogPanel } from "./DecisionLogPanel";
import { ReviewQueuePanel } from "./ReviewQueuePanel";
import { WorkflowMetricsPanel } from "./WorkflowMetricsPanel";
import { WorkflowTaskPanel } from "./WorkflowTaskPanel";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { Input } from "../ui/Input";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";
import { Select } from "../ui/Select";

interface WorkflowDashboardProps {
  caseId: string;
}

export function WorkflowDashboard({ caseId }: WorkflowDashboardProps) {
  const query = useDecisionSupportQuery(caseId);
  const generateMutation = useGenerateDecisionSupportMutation(caseId);
  const decisionsQuery = useDecisionSupportDecisionsQuery(caseId);
  const updateTaskMutation = useUpdateWorkflowTaskMutation(caseId);
  const createDecisionMutation = useCreateDecisionMutation(caseId);
  const [search, setSearch] = useState("");
  const [stageFilter, setStageFilter] = useState("all");

  const isNotFound =
    query.error instanceof ApiClientError && query.error.status === 404;
  const run = query.data?.data;
  const decisions = decisionsQuery.data?.data?.items ?? [];

  return (
    <div className="space-y-4">
      <Panel
        description="Deterministic investigator workflows, review queues, and decision tracking from investigation intelligence — without re-running AI or making legal conclusions."
        title="Decision Support"
      >
        <div className="space-y-4 p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex flex-wrap gap-2">
              {run ? (
                <>
                  <Badge tone="cyan">{run.status}</Badge>
                  <Badge tone="neutral">{run.current_stage}</Badge>
                  <Badge tone="neutral">{run.task_count} tasks</Badge>
                  <Badge tone="neutral">
                    {(run.metrics.investigation_progress * 100).toFixed(0)}%
                    progress
                  </Badge>
                </>
              ) : (
                <Badge tone="neutral">Not planned</Badge>
              )}
            </div>
            <Button
              disabled={generateMutation.isPending}
              onClick={() => generateMutation.mutate()}
              size="sm"
            >
              <ListTodo size={14} /> Plan workflow
            </Button>
          </div>

          <div className="flex flex-wrap items-end gap-3">
            <label className="block text-xs text-slate-400">
              Search
              <Input
                className="mt-1 w-56"
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Task, evidence, or reason"
                value={search}
              />
            </label>
            <label className="block text-xs text-slate-400">
              Stage
              <Select
                className="mt-1 w-44"
                onChange={(event) => setStageFilter(event.target.value)}
                value={stageFilter}
              >
                <option value="all">All stages</option>
                {(
                  [
                    "NEW",
                    "TRIAGE",
                    "COLLECT",
                    "VERIFY",
                    "COMPARE",
                    "AI_ANALYSIS",
                    "CORRELATE",
                    "REVIEW",
                    "REPORT",
                    "COMPLETE",
                  ] as const
                ).map((stage) => (
                  <option key={stage} value={stage}>
                    {stage}
                  </option>
                ))}
              </Select>
            </label>
          </div>

          {query.isLoading ? (
            <LoadingState label="Loading decision support" />
          ) : null}
          {query.isError && !isNotFound ? (
            <ErrorState
              description="Unable to load decision-support workflow."
              title="Workflow unavailable"
            />
          ) : null}
          {generateMutation.isError ? (
            <ErrorState
              description="Workflow planning failed."
              title="Plan error"
            />
          ) : null}
          {(isNotFound || (!run && !query.isLoading)) &&
          !generateMutation.isPending ? (
            <EmptyState
              description="Plan a workflow to generate tasks and a review queue from existing intelligence."
              title="No decision-support plan"
            />
          ) : null}

          {run?.provenance ? (
            <div className="text-[11px] text-slate-600">
              Provenance · engine {String(run.engine_version)} · policy{" "}
              {String(run.policy_version)}
            </div>
          ) : null}

          {run?.tasks?.[0]?.id ? (
            <Button
              disabled={createDecisionMutation.isPending}
              onClick={() =>
                createDecisionMutation.mutate({
                  decision_type: "MARKED_REVIEWED",
                  investigator: "investigator",
                  justification: "Acknowledged current workflow plan.",
                  task_id: run.tasks[0].id ?? undefined,
                })
              }
              size="sm"
              variant="secondary"
            >
              Log review decision
            </Button>
          ) : null}
        </div>
      </Panel>

      <div className="grid gap-4 xl:grid-cols-2">
        <WorkflowMetricsPanel
          currentStage={run?.current_stage ?? null}
          metrics={run?.metrics ?? null}
        />
        <WorkflowTaskPanel
          onComplete={(taskId) =>
            updateTaskMutation.mutate({ taskId, status: "COMPLETED" })
          }
          search={search}
          stageFilter={stageFilter}
          tasks={run?.tasks ?? []}
        />
        <ReviewQueuePanel items={run?.review_queue ?? []} search={search} />
        <DecisionLogPanel decisions={decisions} />
      </div>
    </div>
  );
}
