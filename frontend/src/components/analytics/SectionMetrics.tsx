import { Panel } from "../ui/Panel";

interface SectionMetricsProps {
  title: string;
  description: string;
  data: Record<string, unknown>;
}

export function SectionMetrics({ title, description, data }: SectionMetricsProps) {
  const rows = Object.entries(data);

  return (
    <Panel description={description} title={title}>
      <div className="space-y-2 p-4 text-xs text-slate-400">
        {rows.length === 0 ? (
          <p className="text-slate-500">No data.</p>
        ) : null}
        <dl className="grid gap-2 sm:grid-cols-2">
          {rows.map(([key, value]) => (
            <div key={key}>
              <dt className="text-slate-600">{key}</dt>
              <dd className="text-slate-200">
                {typeof value === "object" && value !== null
                  ? JSON.stringify(value)
                  : String(value)}
              </dd>
            </div>
          ))}
        </dl>
      </div>
    </Panel>
  );
}
