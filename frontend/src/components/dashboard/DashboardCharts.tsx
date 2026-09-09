import { memo } from "react";

import type { ChartSlice } from "../../hooks/useExecutiveDashboard";
import { cn } from "../../lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";

const toneClass: Record<NonNullable<ChartSlice["tone"]>, string> = {
  primary: "bg-primary",
  success: "bg-success",
  warning: "bg-warning",
  danger: "bg-danger",
  info: "bg-info",
  neutral: "bg-muted",
};

interface DashboardBarChartProps {
  title: string;
  description?: string;
  slices: ChartSlice[];
  emptyLabel?: string;
}

function DashboardBarChartComponent({
  title,
  description,
  slices,
  emptyLabel = "No data yet",
}: DashboardBarChartProps) {
  const max = Math.max(1, ...slices.map((slice) => slice.value));
  const total = slices.reduce((sum, slice) => sum + slice.value, 0);

  return (
    <Card className="min-w-0 duration-fast transition-shadow hover:shadow-md">
      <CardHeader className="flex-col items-start gap-1">
        <CardTitle>{title}</CardTitle>
        {description && (
          <p className="text-caption text-muted">{description}</p>
        )}
      </CardHeader>
      <CardContent>
        {total === 0 ? (
          <p className="py-8 text-center text-caption text-muted">{emptyLabel}</p>
        ) : (
          <ul className="space-y-3" aria-label={title}>
            {slices.map((slice) => (
              <li key={slice.label}>
                <div className="mb-1 flex items-center justify-between gap-2 text-caption">
                  <span className="truncate text-muted">{slice.label}</span>
                  <span className="font-medium text-foreground">{slice.value}</span>
                </div>
                <div className="h-2 overflow-hidden rounded-pill bg-surface-muted">
                  <div
                    className={cn(
                      "h-full rounded-pill duration-normal transition-[width]",
                      toneClass[slice.tone ?? "primary"],
                    )}
                    style={{
                      width: `${Math.max(4, (slice.value / max) * 100)}%`,
                    }}
                  />
                </div>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

export const DashboardBarChart = memo(DashboardBarChartComponent);

interface DashboardSparkChartProps {
  title: string;
  description?: string;
  points: Array<{ label: string; value: number }>;
  emptyLabel?: string;
}

function DashboardSparkChartComponent({
  title,
  description,
  points,
  emptyLabel = "No series yet",
}: DashboardSparkChartProps) {
  const max = Math.max(1, ...points.map((point) => point.value));

  return (
    <Card className="min-w-0 duration-fast transition-shadow hover:shadow-md">
      <CardHeader className="flex-col items-start gap-1">
        <CardTitle>{title}</CardTitle>
        {description && (
          <p className="text-caption text-muted">{description}</p>
        )}
      </CardHeader>
      <CardContent>
        {points.length === 0 ? (
          <p className="py-8 text-center text-caption text-muted">{emptyLabel}</p>
        ) : (
          <div
            aria-label={title}
            className="flex h-28 items-end gap-1 sm:h-32 sm:gap-1.5"
            role="img"
          >
            {points.map((point) => (
              <div
                className="flex min-w-0 flex-1 flex-col items-center gap-1"
                key={`${point.label}-${point.value}`}
              >
                <div
                  className="w-full rounded-t bg-primary/50 duration-fast transition-[height] hover:bg-primary"
                  style={{
                    height: `${Math.max(8, (point.value / max) * 100)}%`,
                  }}
                  title={`${point.label}: ${point.value}`}
                />
                <span className="max-w-full truncate text-[10px] text-subtle">
                  {point.label}
                </span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export const DashboardSparkChart = memo(DashboardSparkChartComponent);
