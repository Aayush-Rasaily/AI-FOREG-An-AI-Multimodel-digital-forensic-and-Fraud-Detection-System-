import type { PlatformHealthStatus } from "../../types/monitoring";
import { Badge } from "../ui/Badge";
import { Panel } from "../ui/Panel";

const toneByStatus: Record<
  PlatformHealthStatus,
  "success" | "warning" | "error" | "neutral"
> = {
  HEALTHY: "success",
  DEGRADED: "warning",
  WARNING: "warning",
  CRITICAL: "error",
};

interface SystemHealthCardProps {
  status: string;
  reasons: string[];
  assessedAt?: string;
}

export function SystemHealthCard({
  status,
  reasons,
  assessedAt,
}: SystemHealthCardProps) {
  const tone =
    toneByStatus[status as PlatformHealthStatus] ?? ("neutral" as const);
  return (
    <Panel description="Deterministic platform health from persisted job and AI outcomes." title="System Health">
      <div className="space-y-3 p-4">
        <Badge tone={tone}>Health: {status}</Badge>
        <ul className="space-y-1 text-xs text-muted">
          {reasons.map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>
        {assessedAt ? (
          <p className="text-[11px] text-subtle">
            Assessed {new Date(assessedAt).toLocaleString()}
          </p>
        ) : null}
      </div>
    </Panel>
  );
}
