import { useState } from "react";
import { ShieldCheck } from "lucide-react";

import {
  useIntegrityHistoryQuery,
  useIntegrityQuery,
  useRunIntegrityCheckMutation,
} from "../../hooks/useIntegrity";
import { ApiClientError } from "../../services/api/client";
import { AlertPanel } from "./AlertPanel";
import { DriftViewer } from "./DriftViewer";
import { IntegrityTimeline } from "./IntegrityTimeline";
import { VerificationHistory } from "./VerificationHistory";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { Input } from "../ui/Input";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

interface IntegrityDashboardProps {
  caseId: string;
}

export function IntegrityDashboard({ caseId }: IntegrityDashboardProps) {
  const query = useIntegrityQuery(caseId);
  const runMutation = useRunIntegrityCheckMutation(caseId);
  const historyQuery = useIntegrityHistoryQuery(caseId);
  const [search, setSearch] = useState("");

  const isNotFound =
    query.error instanceof ApiClientError && query.error.status === 404;
  const run = query.data?.data;
  const history = historyQuery.data?.data?.items ?? [];

  return (
    <div className="space-y-4">
      <Panel
        description="Continuous, deterministic evidence integrity monitoring — hash, custody, storage, drift, and provenance checks without modifying evidence or re-running AI."
        title="Integrity"
      >
        <div className="space-y-4 p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex flex-wrap gap-2">
              {run ? (
                <>
                  <Badge tone="cyan">{run.status}</Badge>
                  <Badge tone="neutral">
                    {(run.metrics.integrity_score * 100).toFixed(0)}% score
                  </Badge>
                  <Badge tone="amber">{run.alert_count} alerts</Badge>
                  <Badge tone="red">{run.metrics.critical_alerts} critical</Badge>
                  <Badge tone="neutral">{run.drift_count} drift</Badge>
                </>
              ) : (
                <Badge tone="neutral">Not monitored</Badge>
              )}
            </div>
            <Button
              disabled={runMutation.isPending}
              onClick={() => runMutation.mutate()}
              size="sm"
            >
              <ShieldCheck size={14} /> Run integrity check
            </Button>
          </div>

          <label className="block text-xs text-slate-400">
            Search alerts
            <Input
              className="mt-1 w-56"
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Alert, evidence, message"
              value={search}
            />
          </label>

          {query.isLoading ? (
            <LoadingState label="Loading integrity monitor" />
          ) : null}
          {query.isError && !isNotFound ? (
            <ErrorState
              description="Unable to load integrity monitoring results."
              title="Integrity unavailable"
            />
          ) : null}
          {runMutation.isError ? (
            <ErrorState
              description="Integrity check failed."
              title="Monitor error"
            />
          ) : null}
          {(isNotFound || (!run && !query.isLoading)) &&
          !runMutation.isPending ? (
            <EmptyState
              description="Run an integrity check to verify hashes, custody, storage, and provenance from existing records."
              title="No integrity run"
            />
          ) : null}

          {run?.provenance ? (
            <div className="text-[11px] text-slate-600">
              Provenance · engine {String(run.engine_version)} · policy{" "}
              {String(run.policy_version)} · checks {run.check_count}
            </div>
          ) : null}

          {run?.metrics ? (
            <dl className="grid gap-2 text-xs text-slate-400 sm:grid-cols-3">
              <div>
                <dt className="text-slate-600">Passed</dt>
                <dd className="text-slate-200">{run.metrics.checks_passed}</dd>
              </div>
              <div>
                <dt className="text-slate-600">Failed</dt>
                <dd className="text-slate-200">{run.metrics.checks_failed}</dd>
              </div>
              <div>
                <dt className="text-slate-600">Warned</dt>
                <dd className="text-slate-200">{run.metrics.checks_warned}</dd>
              </div>
            </dl>
          ) : null}
        </div>
      </Panel>

      <div className="grid gap-4 xl:grid-cols-2">
        <AlertPanel alerts={run?.alerts ?? []} search={search} />
        <DriftViewer drifts={run?.drifts ?? []} />
        <IntegrityTimeline timeline={run?.timeline ?? []} />
        <VerificationHistory items={history} />
      </div>
    </div>
  );
}
