import { memo } from "react";

import { cn } from "../../lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";

interface ProcessingQueueWidgetProps {
  running: number;
  queued: number;
  completed: number;
  failed: number;
  activeAnalyses: number;
}

function barPercent(value: number, total: number) {
  if (total <= 0) {
    return 0;
  }
  return Math.round((value / total) * 100);
}

function ProcessingQueueWidgetComponent({
  running,
  queued,
  completed,
  failed,
  activeAnalyses,
}: ProcessingQueueWidgetProps) {
  const total = Math.max(1, running + queued + completed + failed);
  const rows = [
    { label: "Running", value: running, className: "bg-primary" },
    { label: "Queued", value: queued, className: "bg-warning" },
    { label: "Completed", value: completed, className: "bg-success" },
    { label: "Failed", value: failed, className: "bg-danger" },
  ];

  return (
    <Card className="min-w-0 duration-fast transition-shadow hover:shadow-md">
      <CardHeader>
        <div>
          <CardTitle>Processing status</CardTitle>
          <p className="mt-1 text-caption text-muted">
            Queue depth and job outcomes · {activeAnalyses} active analyses
          </p>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {rows.map((row) => {
          const pct = barPercent(row.value, total);
          return (
            <div key={row.label}>
              <div className="mb-1 flex justify-between text-caption">
                <span className="text-muted">{row.label}</span>
                <span className="text-foreground">
                  {row.value} · {pct}%
                </span>
              </div>
              <div
                aria-label={`${row.label} ${row.value}`}
                className="h-2.5 overflow-hidden rounded-pill bg-surface-muted"
                role="progressbar"
                aria-valuenow={row.value}
                aria-valuemin={0}
                aria-valuemax={total}
              >
                <div
                  className={cn(
                    "h-full rounded-pill duration-normal transition-[width]",
                    row.className,
                  )}
                  style={{ width: `${Math.max(row.value > 0 ? 6 : 0, pct)}%` }}
                />
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}

export const ProcessingQueueWidget = memo(ProcessingQueueWidgetComponent);
