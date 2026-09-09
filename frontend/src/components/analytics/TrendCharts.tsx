import { Panel } from "../ui/Panel";

interface TrendChartsProps {
  trends: Record<string, Array<{ index: number; label: string; value: number }>>;
}

export function TrendCharts({ trends }: TrendChartsProps) {
  const entries = Object.entries(trends);

  return (
    <Panel
      description="Deterministic series from prior analytics snapshots (not forecasts)."
      title="Trend Charts"
    >
      <div className="space-y-4 p-4">
        {entries.length === 0 ? (
          <p className="text-xs text-muted">No trend data yet.</p>
        ) : null}
        {entries.map(([key, points]) => {
          const max = Math.max(1, ...points.map((p) => p.value));
          return (
            <div key={key}>
              <p className="mb-2 text-xs text-muted">{key}</p>
      <div className="flex h-16 items-end gap-0.5 sm:gap-1">
                {points.map((point) => (
                  <div
                    className="min-w-0 flex-1 rounded-t bg-primary/40 duration-fast transition-[height]"
                    key={`${key}-${point.index}`}
                    style={{
                      height: `${Math.max(8, (point.value / max) * 100)}%`,
                    }}
                    title={`${point.label}: ${point.value}`}
                  />
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </Panel>
  );
}
