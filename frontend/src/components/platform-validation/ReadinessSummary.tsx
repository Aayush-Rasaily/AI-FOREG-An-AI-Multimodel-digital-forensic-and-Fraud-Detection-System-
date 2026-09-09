import { Badge } from "../ui/Badge";
import { Panel } from "../ui/Panel";
import type { PlatformValidationRun } from "../../types/platformValidation";

function toneForLevel(level: string): "success" | "warning" | "error" | "neutral" {
  if (level === "READY") return "success";
  if (level === "DEGRADED") return "warning";
  if (level === "NOT_READY") return "error";
  return "neutral";
}

interface Props {
  run?: PlatformValidationRun | null;
}

export function ReadinessSummary({ run }: Props) {
  if (!run) {
    return (
      <Panel
        description="Run validation to compute a readiness score."
        title="Platform Readiness"
      >
        <div className="p-4 text-sm text-subtle">No validation results yet.</div>
      </Panel>
    );
  }

  return (
    <Panel
      description="Deterministic readiness from migration, API, ORM, and module checks."
      title="Platform Readiness"
    >
      <div className="space-y-3 p-4">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone={toneForLevel(run.readiness_level)}>
            {run.readiness_level}
          </Badge>
          <Badge tone="primary">{run.readiness_score}%</Badge>
          <Badge tone={run.persisted ? "success" : "warning"}>
            {run.persisted ? "persisted" : "live"}
          </Badge>
          <Badge tone="neutral">{run.check_count} checks</Badge>
        </div>
        <div className="grid gap-2 sm:grid-cols-3 text-sm">
          <div>Pass · {run.pass_count}</div>
          <div>Warn · {run.warn_count}</div>
          <div>Fail · {run.fail_count}</div>
        </div>
      </div>
    </Panel>
  );
}
