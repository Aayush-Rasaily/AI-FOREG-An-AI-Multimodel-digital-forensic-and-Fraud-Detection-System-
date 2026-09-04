import type { PlatformHealthStatus } from "../../types/monitoring";
import { Badge } from "../ui/Badge";
import { Panel } from "../ui/Panel";

const toneByStatus: Record<
  PlatformHealthStatus,
  "green" | "amber" | "red" | "neutral"
> = {
  HEALTHY: "green",
  DEGRADED: "amber",
  WARNING: "amber",
  CRITICAL: "red",
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
        <ul className="space-y-1 text-xs text-slate-400">
          {reasons.map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>
        {assessedAt ? (
          <p className="text-[11px] text-slate-600">
            Assessed {new Date(assessedAt).toLocaleString()}
          </p>
        ) : null}
      </div>
    </Panel>
  );
}
