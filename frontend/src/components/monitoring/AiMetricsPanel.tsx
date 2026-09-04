import { Panel } from "../ui/Panel";

interface AiMetricsPanelProps {
  data: Record<string, unknown>;
}

export function AiMetricsPanel({ data }: AiMetricsPanelProps) {
  const modalities = Array.isArray(data.modalities)
    ? (data.modalities as Array<Record<string, unknown>>)
    : [];
  const rankings = Array.isArray(data.detector_failure_rankings)
    ? (data.detector_failure_rankings as Array<Record<string, unknown>>)
    : [];

  return (
    <Panel description="Modality executions, failures, and detector rankings." title="AI Summary">
      <div className="space-y-3 p-4 text-xs">
        <p className="text-slate-400">
          Model executions: {String(data.model_executions ?? 0)} · Failures:{" "}
          {String(data.total_failures ?? 0)} · Unavailable:{" "}
          {String(data.total_unavailable ?? 0)}
        </p>
        <ul className="space-y-1">
          {modalities.map((item) => (
            <li
              className="flex justify-between rounded border border-slate-800 px-2 py-1 text-slate-300"
              key={String(item.modality)}
            >
              <span>{String(item.modality)}</span>
              <span>
                {String(item.executions ?? 0)} runs / {String(item.failures ?? 0)}{" "}
                fail
              </span>
            </li>
          ))}
        </ul>
        {rankings.length > 0 ? (
          <div>
            <p className="mb-1 text-slate-500">Detector failure rankings</p>
            <ul className="space-y-1">
              {rankings.slice(0, 5).map((item) => (
                <li key={String(item.modality)} className="text-slate-400">
                  {String(item.modality)}: {String(item.failures ?? 0)} (
                  {String(item.failure_rate ?? 0)})
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>
    </Panel>
  );
}
