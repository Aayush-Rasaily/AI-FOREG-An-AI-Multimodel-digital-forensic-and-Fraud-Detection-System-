import { Panel } from "../ui/Panel";

interface KpiCardsProps {
  items: Array<{ key: string; label: string; value: number; unit: string }>;
}

export function KpiCards({ items }: KpiCardsProps) {
  return (
    <Panel description="Key operational metrics from persisted data." title="KPI Cards">
      <div className="grid grid-cols-1 gap-3 p-4 sm:grid-cols-2 lg:grid-cols-3 desktop:grid-cols-4">
        {items.length === 0 ? (
          <p className="text-xs text-muted">No KPIs yet.</p>
        ) : null}
        {items.map((item) => (
          <div
            className="rounded-lg border border-border bg-background/40 p-3"
            key={item.key}
          >
            <p className="text-[11px] uppercase tracking-wide text-muted">
              {item.label}
            </p>
            <p className="mt-1 text-lg text-foreground">
              {item.unit === "ratio"
                ? `${(item.value * 100).toFixed(0)}%`
                : item.unit === "bytes"
                  ? `${(item.value / (1024 * 1024)).toFixed(2)} MB`
                  : String(item.value)}
            </p>
          </div>
        ))}
      </div>
    </Panel>
  );
}
