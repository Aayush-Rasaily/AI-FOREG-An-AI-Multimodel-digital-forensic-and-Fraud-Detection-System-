import { Panel } from "../ui/Panel";

interface Props {
  compatibility?: Record<string, unknown> | null;
}

export function CompatibilityPanel({ compatibility }: Props) {
  const modules =
    (compatibility?.modules as Record<string, string> | undefined) ?? {};
  const entries = Object.entries(modules);

  return (
    <Panel
      description="Engine version compatibility across Phase 9 modules."
      title="Compatibility Panel"
    >
      <div className="space-y-2 p-4 text-sm">
        <div className="text-xs text-slate-500">
          AI re-run: {String(compatibility?.ai_rerun ?? false)} · Forecasting:{" "}
          {String(compatibility?.forecasting ?? false)}
        </div>
        {entries.length === 0 ? (
          <p className="text-slate-600">No module versions available.</p>
        ) : (
          entries.map(([name, version]) => (
            <div
              className="flex justify-between border-b border-slate-100 py-1"
              key={name}
            >
              <span>{name}</span>
              <span className="font-mono text-xs">{version}</span>
            </div>
          ))
        )}
      </div>
    </Panel>
  );
}
