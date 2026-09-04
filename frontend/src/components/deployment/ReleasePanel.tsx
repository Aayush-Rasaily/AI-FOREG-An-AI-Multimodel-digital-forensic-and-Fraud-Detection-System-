import { Badge } from "../ui/Badge";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";
import { useSystemReleaseQuery } from "../../hooks/useSystemStatus";

export function ReleasePanel() {
  const query = useSystemReleaseQuery();

  if (query.isLoading) {
    return <LoadingState label="Loading release metadata" />;
  }
  if (query.isError) {
    return (
      <ErrorState
        description="Unable to load release metadata."
        title="Release unavailable"
      />
    );
  }

  const release = query.data?.data;
  if (!release) {
    return (
      <EmptyState
        description="No release metadata was returned by the API."
        title="No release data"
      />
    );
  }

  const policies = Object.entries(release.policy_versions);
  const engines = Object.entries(release.ai_engine_versions);

  return (
    <Panel
      description="Application, schema, policy, and build identity for this deployment."
      title="Release"
    >
      <div className="space-y-4 p-4 text-sm">
        <div className="flex flex-wrap gap-2">
          <Badge tone="green">v{release.application_version}</Badge>
          <Badge tone="neutral">{release.environment}</Badge>
          <Badge tone="neutral">schema {release.schema_version}</Badge>
        </div>
        <dl className="grid gap-2 text-xs text-slate-400 sm:grid-cols-2">
          <div>
            <dt className="text-slate-600">Migration</dt>
            <dd className="text-slate-200">{release.migration_version}</dd>
          </div>
          <div>
            <dt className="text-slate-600">Git commit</dt>
            <dd className="font-mono text-slate-200">
              {release.git_commit ?? "unavailable"}
            </dd>
          </div>
        </dl>
        <div>
          <p className="mb-2 text-[11px] uppercase tracking-wide text-slate-600">
            Policy versions
          </p>
          {policies.length ? (
            <ul className="space-y-1 text-xs text-slate-400">
              {policies.map(([key, value]) => (
                <li key={key}>
                  <span className="text-slate-300">{key}</span>: {value}
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState description="No policy versions registered." title="Empty" />
          )}
        </div>
        <div>
          <p className="mb-2 text-[11px] uppercase tracking-wide text-slate-600">
            AI engines
          </p>
          {engines.length ? (
            <ul className="space-y-1 text-xs text-slate-400">
              {engines.map(([key, value]) => (
                <li key={key}>
                  <span className="text-slate-300">{key}</span>: {value}
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState
              description="No AI engine markers exposed for this process."
              title="Empty"
            />
          )}
        </div>
      </div>
    </Panel>
  );
}
