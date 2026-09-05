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
          <p className="text-xs text-slate-500">No trend data yet.</p>
        ) : null}
        {entries.map(([key, points]) => {
          const max = Math.max(1, ...points.map((p) => p.value));
          return (
            <div key={key}>
              <p className="mb-2 text-xs text-slate-400">{key}</p>
              <div className="flex h-16 items-end gap-1">
                {points.map((point) => (
                  <div
                    className="flex-1 rounded-t bg-cyan-400/40"
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
