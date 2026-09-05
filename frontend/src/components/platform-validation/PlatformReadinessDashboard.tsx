import { HeartPulse, RefreshCw } from "lucide-react";

import {
  usePlatformValidationLatestQuery,
  useRunPlatformValidationMutation,
} from "../../hooks/usePlatformValidation";
import { CompatibilityPanel } from "./CompatibilityPanel";
import { HealthReportPanel } from "./HealthReportPanel";
import { IssueViewer } from "./IssueViewer";
import { ReadinessSummary } from "./ReadinessSummary";
import { ValidationResults } from "./ValidationResults";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";
import { PageHeader } from "../layout/PageHeader";

export function PlatformReadinessDashboard() {
  const query = usePlatformValidationLatestQuery();
  const validateMutation = useRunPlatformValidationMutation();
  const run = query.data?.data;

  return (
    <div className="space-y-4">
      <PageHeader
        description="Deterministic end-to-end validation across migrations, APIs, modules, and configuration — no AI re-runs."
        eyebrow="Operations"
        title="Platform Health"
      />

      <Panel
        description="Execute the Phase 9H readiness catalog and persist results."
        title="Platform Readiness Dashboard"
      >
        <div className="space-y-4 p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex flex-wrap gap-2">
              {run ? (
                <>
                  <Badge tone="cyan">{run.status}</Badge>
                  <Badge tone="neutral">
                    engine {run.engine_version}
                  </Badge>
                </>
              ) : (
                <Badge tone="neutral">No run</Badge>
              )}
            </div>
            <Button
              disabled={validateMutation.isPending}
              onClick={() => validateMutation.mutate()}
              size="sm"
            >
              <RefreshCw size={14} /> Run validation
            </Button>
          </div>

          {query.isLoading ? (
            <LoadingState label="Loading platform validation" />
          ) : null}
          {query.isError ? (
            <ErrorState
              description="Unable to load platform validation."
              title="Validation unavailable"
            />
          ) : null}
          {validateMutation.isError ? (
            <ErrorState
              description="Platform validation failed to execute."
              title="Validation error"
            />
          ) : null}
        </div>
      </Panel>

      <ReadinessSummary run={run} />

      <div className="grid gap-4 xl:grid-cols-2">
        <ValidationResults results={run?.results ?? []} />
        <IssueViewer issues={run?.issues ?? []} />
        <HealthReportPanel report={run?.health_report ?? {}} />
        <CompatibilityPanel compatibility={run?.compatibility ?? {}} />
      </div>

      <div className="flex items-center gap-2 text-xs text-slate-600">
        <HeartPulse size={14} /> Readiness only — no forecasting or model
        execution.
      </div>
    </div>
  );
}
