import { ShieldCheck } from "lucide-react";

import {
  useRunDiagnosticsMutation,
  useSystemDiagnosticsQuery,
} from "../../hooks/useSystem";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

const STATUS_TONE: Record<
  string,
  "success" | "warning" | "error" | "neutral"
> = {
  PASS: "success",
  WARN: "warning",
  FAIL: "error",
  SKIP: "neutral",
};

export function DiagnosticsPanel() {
  const query = useSystemDiagnosticsQuery();
  const runMutation = useRunDiagnosticsMutation();
  const data = query.data?.data;

  return (
    <Panel
      description="Configuration, dependency, and infrastructure checks."
      title="Diagnostics"
    >
      <div className="p-4 space-y-3">
        <Button
          disabled={runMutation.isPending}
          onClick={() => runMutation.mutate()}
          size="sm"
          variant="secondary"
        >
          <ShieldCheck size={14} />
          {runMutation.isPending ? "Running…" : "Run Diagnostics"}
        </Button>

        {(query.isLoading || runMutation.isPending) && (
          <LoadingState label="Running diagnostics…" />
        )}
        {query.isError && (
          <ErrorState
            description="Diagnostics unavailable."
            onRetry={() => void query.refetch()}
            title="Diagnostics failed"
          />
        )}
        {data && (
          <>
            <Badge
              tone={
                data.overall_status === "healthy"
                  ? "success"
                  : data.overall_status === "unhealthy"
                    ? "error"
                    : "warning"
              }
            >
              {data.overall_status}
            </Badge>
            <ul className="space-y-1 text-xs">
              {data.checks.map((check) => (
                <li
                  className="flex items-center gap-2 rounded border border-border px-2 py-1.5"
                  key={check.name}
                >
                  <Badge tone={STATUS_TONE[check.status] ?? "neutral"}>
                    {check.status}
                  </Badge>
                  <span className="text-muted">{check.name}</span>
                  <span className="ml-auto text-muted">
                    {check.detail}
                  </span>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </Panel>
  );
}
