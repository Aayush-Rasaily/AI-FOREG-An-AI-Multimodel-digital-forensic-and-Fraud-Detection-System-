import { memo } from "react";

import type { CasePriority } from "../../types/case";
import { cn } from "../../lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";

const cells: Array<{
  key: CasePriority;
  label: string;
  className: string;
}> = [
  {
    key: "LOW",
    label: "Low",
    className: "bg-success-soft text-success border-success/30",
  },
  {
    key: "MEDIUM",
    label: "Medium",
    className: "bg-info-soft text-info border-info/30",
  },
  {
    key: "HIGH",
    label: "High",
    className: "bg-warning-soft text-warning border-warning/30",
  },
  {
    key: "CRITICAL",
    label: "Critical",
    className: "bg-danger-soft text-danger border-danger/30",
  },
];

function RiskHeatmapComponent({
  counts,
}: {
  counts: Record<CasePriority, number>;
}) {
  const max = Math.max(1, ...Object.values(counts));

  return (
    <Card className="min-w-0 duration-fast transition-shadow hover:shadow-md">
      <CardHeader>
        <div>
          <CardTitle>Risk heatmap</CardTitle>
          <p className="mt-1 text-caption text-muted">
            Case priority distribution · color coded
          </p>
        </div>
      </CardHeader>
      <CardContent>
        <div
          aria-label="Risk heatmap"
          className="grid grid-cols-2 gap-2 sm:grid-cols-4"
          role="list"
        >
          {cells.map((cell) => {
            const value = counts[cell.key];
            const intensity = 0.35 + (value / max) * 0.65;
            return (
              <div
                className={cn(
                  "flex min-h-24 flex-col justify-between rounded-xl border p-3",
                  cell.className,
                )}
                key={cell.key}
                role="listitem"
                style={{ opacity: intensity }}
              >
                <span className="text-caption font-medium">{cell.label}</span>
                <span className="text-2xl font-semibold tabular-nums">
                  {value}
                </span>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

export const RiskHeatmap = memo(RiskHeatmapComponent);
