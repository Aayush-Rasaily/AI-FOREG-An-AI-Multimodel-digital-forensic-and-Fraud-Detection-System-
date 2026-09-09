import { memo } from "react";
import { Database, Server, ShieldCheck } from "lucide-react";

import type { HealthStatus } from "../../types/api";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";
import { StatusIndicator } from "../ui/StatusIndicator";

type Tone = "online" | "offline" | "pending" | "warning";

function mapHealth(raw: string | undefined): { label: string; tone: Tone } {
  const value = (raw ?? "").toLowerCase();
  if (!value) {
    return { label: "Awaiting signal", tone: "pending" };
  }
  if (value === "ok" || value === "healthy" || value === "up") {
    return { label: "Healthy", tone: "online" };
  }
  if (value === "degraded" || value === "warn") {
    return { label: "Degraded", tone: "warning" };
  }
  return { label: raw ?? "Unknown", tone: "offline" };
}

interface SystemStatusCardProps {
  health?: HealthStatus | null;
  loading?: boolean;
  error?: boolean;
  jobsConnected?: boolean;
  activeAnalyses?: number;
}

function SystemStatusCardComponent({
  health,
  loading,
  error,
  jobsConnected,
  activeAnalyses = 0,
}: SystemStatusCardProps) {
  const api = loading
    ? { label: "Checking…", tone: "pending" as Tone }
    : error
      ? { label: "Unreachable", tone: "offline" as Tone }
      : mapHealth(health?.status);

  const database = mapHealth(health?.database);
  const workers = jobsConnected
    ? {
        label: activeAnalyses > 0 ? `${activeAnalyses} active` : "Connected",
        tone: "online" as Tone,
      }
    : { label: "Not connected", tone: "offline" as Tone };

  return (
    <Card className="min-w-0 duration-fast transition-shadow hover:shadow-md">
      <CardHeader>
        <div>
          <CardTitle>System status</CardTitle>
          <p className="mt-1 text-xs text-muted">
            Operational signals from connected services
          </p>
        </div>
        <ShieldCheck aria-hidden="true" className="text-subtle" size={17} />
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center justify-between rounded-lg border border-border bg-background/60 px-3 py-3">
          <div className="flex items-center gap-3">
            <Server aria-hidden="true" className="text-muted" size={16} />
            <span className="text-xs text-muted">Application API</span>
          </div>
          <StatusIndicator label={api.label} tone={api.tone} />
        </div>
        <div className="flex items-center justify-between rounded-lg border border-border bg-background/60 px-3 py-3">
          <div className="flex items-center gap-3">
            <Database aria-hidden="true" className="text-muted" size={16} />
            <span className="text-xs text-muted">Database</span>
          </div>
          <StatusIndicator label={database.label} tone={database.tone} />
        </div>
        <div className="flex items-center justify-between rounded-lg border border-border bg-background/60 px-3 py-3">
          <div className="flex items-center gap-3">
            <span className="h-2 w-2 rounded-full bg-surface-muted" />
            <span className="text-xs text-muted">Analysis workers</span>
          </div>
          <StatusIndicator label={workers.label} tone={workers.tone} />
        </div>
        {health?.version && (
          <p className="text-micro text-subtle">
            API {health.version} · {health.environment}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

export const SystemStatusCard = memo(SystemStatusCardComponent);
