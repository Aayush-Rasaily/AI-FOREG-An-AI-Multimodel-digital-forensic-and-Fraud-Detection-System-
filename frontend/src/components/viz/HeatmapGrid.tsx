import { memo } from "react";

import { cn } from "../../lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";

export interface HeatCell {
  id: string;
  label: string;
  value: number;
  tone?: "success" | "info" | "warning" | "danger" | "primary";
}

const toneBg: Record<NonNullable<HeatCell["tone"]>, string> = {
  success: "bg-success-soft text-success border-success/30",
  info: "bg-info-soft text-info border-info/30",
  warning: "bg-warning-soft text-warning border-warning/30",
  danger: "bg-danger-soft text-danger border-danger/30",
  primary: "bg-primary-soft text-primary border-primary/30",
};

interface HeatmapGridProps {
  title: string;
  description?: string;
  cells: HeatCell[];
  columns?: number;
  onSelect?: (cell: HeatCell) => void;
  selectedId?: string | null;
}

function HeatmapGridComponent({
  title,
  description,
  cells,
  columns = 4,
  onSelect,
  selectedId,
}: HeatmapGridProps) {
  const max = Math.max(1, ...cells.map((c) => c.value));

  return (
    <Card className="min-w-0">
      <CardHeader className="flex-col items-start gap-1">
        <CardTitle>{title}</CardTitle>
        {description && (
          <p className="text-caption text-muted">{description}</p>
        )}
      </CardHeader>
      <CardContent>
        {cells.length === 0 ? (
          <p className="py-8 text-center text-caption text-muted">
            No heatmap data
          </p>
        ) : (
          <div
            aria-label={title}
            className={cn(
              "grid gap-2",
              columns <= 2 && "grid-cols-2",
              columns === 3 && "grid-cols-2 sm:grid-cols-3",
              columns >= 4 && "grid-cols-2 sm:grid-cols-4",
            )}
            role="list"
          >
            {cells.map((cell) => {
              const intensity = 0.4 + (cell.value / max) * 0.6;
              return (
                <button
                  aria-pressed={selectedId === cell.id}
                  className={cn(
                    "flex min-h-20 flex-col justify-between rounded-xl border p-3 text-left duration-fast transition-shadow hover:shadow-md",
                    toneBg[cell.tone ?? "primary"],
                    selectedId === cell.id && "ring-2 ring-ring",
                  )}
                  key={cell.id}
                  onClick={() => onSelect?.(cell)}
                  role="listitem"
                  style={{ opacity: intensity }}
                  type="button"
                >
                  <span className="text-caption font-medium">{cell.label}</span>
                  <span className="text-2xl font-semibold tabular-nums">
                    {cell.value}
                  </span>
                </button>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export const HeatmapGrid = memo(HeatmapGridComponent);
