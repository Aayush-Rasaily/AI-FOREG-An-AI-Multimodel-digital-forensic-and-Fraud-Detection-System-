import type { SystemCheckItem } from "../../types/system";
import { Badge } from "../ui/Badge";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";
import {
  useSystemLivenessQuery,
  useSystemReadinessQuery,
  useSystemStartupValidationQuery,
} from "../../hooks/useSystemStatus";

function statusTone(
  status: string,
): "green" | "amber" | "red" | "neutral" {
  const normalized = status.toUpperCase();
  if (
    normalized === "ALIVE" ||
    normalized === "READY" ||
    normalized === "PASSED" ||
    normalized === "PASS"
  ) {
    return "green";
  }
  if (
    normalized === "DEGRADED" ||
    normalized === "WARN" ||
    normalized === "PARTIAL" ||
    normalized === "NOT_READY"
  ) {
    return "amber";
  }
  if (
    normalized === "FAILED" ||
    normalized === "FAIL" ||
    normalized === "NOT READY"
  ) {
    return "red";
  }
  return "neutral";
}

function CheckList({ checks }: { checks: SystemCheckItem[] }) {
  if (!checks.length) {
    return (
      <EmptyState
        description="No readiness checks have been reported yet."
        title="No checks"
      />
    );
  }
  return (
    <ul className="space-y-2">
      {checks.map((item) => (
        <li
          className="flex items-start justify-between gap-3 text-xs"
          key={item.check}
        >
          <div>
            <p className="font-medium text-slate-200">{item.check}</p>
            <p className="text-slate-500">{item.message}</p>
          </div>
          <Badge tone={statusTone(item.status)}>{item.status}</Badge>
        </li>
      ))}
    </ul>
  );
}

export function HealthOverview() {
  const liveness = useSystemLivenessQuery();
  const readiness = useSystemReadinessQuery();
  const startup = useSystemStartupValidationQuery();

  if (liveness.isLoading || readiness.isLoading || startup.isLoading) {
    return <LoadingState label="Loading health overview" />;
  }

  if (liveness.isError || readiness.isError || startup.isError) {
    return (
      <ErrorState
        description="Unable to load deployment health probes."
        title="Health overview unavailable"
      />
    );
  }

  const live = liveness.data?.data;
  const ready = readiness.data?.data;
  const start = startup.data?.data;

  return (
    <Panel
      description="Liveness, readiness, and startup validation for production probes."
      title="Health Overview"
    >
      <div className="space-y-4 p-4">
        <div className="flex flex-wrap gap-2">
          <Badge tone={statusTone(live?.status ?? "")}>
            Liveness: {live?.status ?? "unknown"}
          </Badge>
          <Badge tone={statusTone(ready?.status ?? "")}>
            Readiness: {ready?.status ?? "unknown"}
          </Badge>
          <Badge tone={statusTone(start?.status ?? "")}>
            Startup: {start?.status ?? "unknown"}
          </Badge>
        </div>
        <div>
          <p className="mb-2 text-[11px] uppercase tracking-wide text-slate-600">
            Readiness checks
          </p>
          <CheckList checks={ready?.checks ?? []} />
        </div>
        {start ? (
          <p className="text-[11px] text-slate-600">
            Startup validation at {new Date(start.timestamp).toLocaleString()}
            {start.graceful_shutdown_supported
              ? " · graceful shutdown supported"
              : ""}
          </p>
        ) : null}
      </div>
    </Panel>
  );
}
