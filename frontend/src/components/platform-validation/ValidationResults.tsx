import { Badge } from "../ui/Badge";
import { Panel } from "../ui/Panel";
import type { ValidationResult } from "../../types/platformValidation";

function toneForStatus(status: string): "green" | "amber" | "red" | "neutral" {
  if (status === "PASS") return "green";
  if (status === "WARN") return "amber";
  if (status === "FAIL") return "red";
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
          <p className="text-sm text-slate-600">No check results.</p>
        ) : (
          results.map((item) => (
            <div
              className="flex flex-wrap items-start justify-between gap-2 border-b border-slate-200 pb-2 text-sm"
              key={item.check_key}
            >
              <div>
                <div className="font-medium text-slate-800">{item.label}</div>
                <div className="text-xs text-slate-500">
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
