import { Badge } from "../ui/Badge";
import { Panel } from "../ui/Panel";
import type { ValidationResult } from "../../types/platformValidation";

function toneForStatus(status: string): "success" | "warning" | "error" | "neutral" {
  if (status === "PASS") return "success";
  if (status === "WARN") return "warning";
  if (status === "FAIL") return "error";
  return "neutral";
}

interface Props {
  results: ValidationResult[];
}

export function ValidationResults({ results }: Props) {
  return (
    <Panel
      description="Ordered catalog of platform checks — no AI re-runs or data mutation."
      title="Validation Results"
    >
      <div className="max-h-96 space-y-2 overflow-auto p-4">
        {results.length === 0 ? (
          <p className="text-sm text-subtle">No check results.</p>
        ) : (
          results.map((item) => (
            <div
              className="flex flex-wrap items-start justify-between gap-2 border-b border-border pb-2 text-sm"
              key={item.check_key}
            >
              <div>
                <div className="font-medium text-foreground">{item.label}</div>
                <div className="text-xs text-muted">
                  {item.category} · {item.message}
                </div>
              </div>
              <Badge tone={toneForStatus(item.status)}>{item.status}</Badge>
            </div>
          ))
        )}
      </div>
    </Panel>
  );
}
