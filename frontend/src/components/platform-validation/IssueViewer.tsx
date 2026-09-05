import { Badge } from "../ui/Badge";
import { Panel } from "../ui/Panel";
import type { ValidationIssue } from "../../types/platformValidation";

function toneForSeverity(
  severity: string,
): "green" | "amber" | "red" | "neutral" {
  if (severity === "WARN") return "amber";
  if (severity === "FAIL") return "red";
  return "neutral";
}

interface Props {
  issues: ValidationIssue[];
}

export function IssueViewer({ issues }: Props) {
  return (
    <Panel
      description="Warnings and failures from the latest validation run."
      title="Issue Viewer"
    >
      <div className="max-h-80 space-y-2 overflow-auto p-4">
        {issues.length === 0 ? (
          <p className="text-sm text-slate-600">No issues reported.</p>
        ) : (
          issues.map((item) => (
            <div
              className="rounded border border-slate-200 p-2 text-sm"
              key={`${item.check_key}-${item.severity}`}
            >
              <div className="mb-1 flex items-center gap-2">
                <Badge tone={toneForSeverity(item.severity)}>
                  {item.severity}
                </Badge>
                <span className="font-medium">{item.check_key}</span>
              </div>
              <p className="text-xs text-slate-600">{item.message}</p>
            </div>
          ))
        )}
      </div>
    </Panel>
  );
}
