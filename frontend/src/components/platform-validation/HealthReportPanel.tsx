import { Panel } from "../ui/Panel";

interface Props {
  report?: Record<string, unknown> | null;
}

export function HealthReportPanel({ report }: Props) {
  const counts = (report?.counts as Record<string, number> | undefined) ?? {};
  const categories =
    (report?.categories as Record<string, unknown[]> | undefined) ?? {};

  return (
    <Panel
      description="Aggregated health categories from platform validation."
      title="Health Report"
    >
      <div className="space-y-3 p-4 text-sm">
        {!report || Object.keys(report).length === 0 ? (
          <p className="text-slate-600">No health report yet.</p>
        ) : (
          <>
            <div className="grid gap-2 sm:grid-cols-4">
              <div>Total · {counts.total ?? 0}</div>
              <div>Pass · {counts.pass ?? 0}</div>
              <div>Warn · {counts.warn ?? 0}</div>
              <div>Fail · {counts.fail ?? 0}</div>
            </div>
            <div className="space-y-1">
              {Object.keys(categories)
                .sort()
                .map((category) => (
                  <div className="text-xs text-slate-600" key={category}>
                    {category}: {categories[category]?.length ?? 0} checks
                  </div>
                ))}
            </div>
          </>
        )}
      </div>
    </Panel>
  );
}
