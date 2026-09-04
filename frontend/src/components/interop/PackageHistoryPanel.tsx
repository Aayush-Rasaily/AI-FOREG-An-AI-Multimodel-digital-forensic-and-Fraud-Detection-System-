import { IntegrityBadge } from "./IntegrityBadge";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";
import { useExportsQuery, useImportsQuery } from "../../hooks/useInteroperability";

interface PackageHistoryPanelProps {
  caseId?: string;
  onSelectExport?: (exportId: string) => void;
}

export function PackageHistoryPanel({
  caseId,
  onSelectExport,
}: PackageHistoryPanelProps) {
  const exportsQuery = useExportsQuery(caseId);
  const importsQuery = useImportsQuery();

  if (exportsQuery.isLoading || importsQuery.isLoading) {
    return <LoadingState label="Loading package history" />;
  }
  if (exportsQuery.isError || importsQuery.isError) {
    return (
      <ErrorState
        description="Unable to load export and import history."
        title="History unavailable"
      />
    );
  }

  const exports = exportsQuery.data?.data.items ?? [];
  const imports = importsQuery.data?.data.items ?? [];

  return (
    <Panel
      description="Recent investigation package exchange jobs."
      title="Package History"
    >
      <div className="grid gap-4 p-4 xl:grid-cols-2">
        <div>
          <p className="mb-2 text-[11px] uppercase tracking-wide text-slate-600">
            Exports
          </p>
          {!exports.length ? (
            <EmptyState
              description="No export jobs yet."
              title="Empty"
            />
          ) : (
            <ul className="space-y-2 text-xs text-slate-400">
              {exports.map((item) => (
                <li key={item.id}>
                  <button
                    className="flex w-full items-center justify-between gap-2 text-left hover:text-cyan-300"
                    onClick={() => onSelectExport?.(item.id)}
                    type="button"
                  >
                    <span>
                      {item.format} ·{" "}
                      {new Date(item.created_at).toLocaleString()}
                    </span>
                    <IntegrityBadge status={item.status} />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div>
          <p className="mb-2 text-[11px] uppercase tracking-wide text-slate-600">
            Imports
          </p>
          {!imports.length ? (
            <EmptyState
              description="No import jobs yet."
              title="Empty"
            />
          ) : (
            <ul className="space-y-2 text-xs text-slate-400">
              {imports.map((item) => (
                <li
                  className="flex items-center justify-between gap-2"
                  key={item.id}
                >
                  <span>{item.source_filename ?? item.id}</span>
                  <IntegrityBadge status={item.integrity_status} />
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </Panel>
  );
}
