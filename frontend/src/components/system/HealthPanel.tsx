import { Activity, Database, HardDrive, Server } from "lucide-react";

import { useSystemHealthQuery } from "../../hooks/useSystem";
import { Badge } from "../ui/Badge";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

function tone(status: string): "success" | "warning" | "error" | "neutral" {
  if (status === "healthy") return "success";
  if (status === "degraded") return "warning";
  if (status === "unavailable") return "error";
  return "neutral";
}

export function HealthPanel() {
  const query = useSystemHealthQuery();
  const data = query.data?.data;

  return (
    <Panel description="Service, database, and resource health." title="Health">
      <div className="p-4">
        {query.isLoading && <LoadingState label="Checking health…" />}
        {query.isError && (
          <ErrorState
            description="Health snapshot unavailable."
            onRetry={() => void query.refetch()}
            title="Health check failed"
          />
        )}
        {data && (
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-lg border border-border bg-background/40 p-3">
              <div className="mb-2 flex items-center gap-2 text-xs text-muted">
                <Server size={14} /> Service
              </div>
              <Badge tone={tone(data.status)}>{data.status}</Badge>
              <p className="mt-2 text-xs text-muted">
                {data.service} v{data.version}
              </p>
            </div>
            <div className="rounded-lg border border-border bg-background/40 p-3">
              <div className="mb-2 flex items-center gap-2 text-xs text-muted">
                <Database size={14} /> Database
              </div>
              <Badge tone={tone(data.database.status)}>
                {data.database.status}
              </Badge>
            </div>
            <div className="rounded-lg border border-border bg-background/40 p-3">
              <div className="mb-2 flex items-center gap-2 text-xs text-muted">
                <Activity size={14} /> Redis
              </div>
              <Badge tone={tone(data.redis.status)}>
                {data.redis.status}
              </Badge>
            </div>
            <div className="rounded-lg border border-border bg-background/40 p-3">
              <div className="mb-2 flex items-center gap-2 text-xs text-muted">
                <HardDrive size={14} /> Resources
              </div>
              <p className="text-xs text-muted">
                CPU: {data.resources.cpu_percent ?? "—"}%
              </p>
              <p className="text-xs text-muted">
                Memory: {data.resources.memory_mb ?? "—"} MB
              </p>
              <p className="text-xs text-muted">
                Uptime: {Math.round(data.uptime_seconds)}s
              </p>
            </div>
          </div>
        )}
      </div>
    </Panel>
  );
}
