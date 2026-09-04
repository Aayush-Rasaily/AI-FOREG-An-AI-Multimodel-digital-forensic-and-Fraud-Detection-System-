import { useState } from "react";
import { Download, Package } from "lucide-react";

import {
  useExportCaseMutation,
  useExportsQuery,
} from "../../hooks/useInteroperability";
import { interoperabilityApi } from "../../services/api/interoperability";
import type { ExportFormat } from "../../types/interoperability";
import { IntegrityBadge } from "./IntegrityBadge";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";
import { Select } from "../ui/Select";

const FORMATS: { value: ExportFormat; label: string }[] = [
  { value: "json_package", label: "JSON Investigation Package" },
  { value: "csv", label: "CSV" },
  { value: "pdf_bundle", label: "PDF Report Bundle" },
  { value: "zip_evidence", label: "ZIP Evidence Package" },
  { value: "manifest", label: "Manifest Package" },
];

interface ExportPanelProps {
  caseId: string;
  onSelectExport?: (exportId: string) => void;
}

export function ExportPanel({ caseId, onSelectExport }: ExportPanelProps) {
  const [format, setFormat] = useState<ExportFormat>("json_package");
  const [includeBinaries, setIncludeBinaries] = useState(false);
  const exportsQuery = useExportsQuery(caseId);
  const exportMutation = useExportCaseMutation(caseId);

  return (
    <Panel
      description="Export investigation packages with deterministic manifests and checksums."
      title="Export"
    >
      <div className="space-y-4 p-4">
        <div className="flex flex-wrap items-end gap-3">
          <label className="block text-xs text-slate-400">
            Format
            <Select
              className="mt-1 w-56"
              onChange={(event) =>
                setFormat(event.target.value as ExportFormat)
              }
              value={format}
            >
              {FORMATS.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </Select>
          </label>
          <label className="flex items-center gap-2 text-xs text-slate-400">
            <input
              checked={includeBinaries}
              onChange={(event) => setIncludeBinaries(event.target.checked)}
              type="checkbox"
            />
            Include binaries
          </label>
          <Button
            disabled={exportMutation.isPending}
            onClick={() =>
              exportMutation.mutate({
                format,
                include_binaries: includeBinaries,
              })
            }
            size="sm"
          >
            <Package size={14} /> Create package
          </Button>
        </div>

        {exportMutation.isError ? (
          <ErrorState
            description="Export request failed."
            title="Export error"
          />
        ) : null}
        {exportMutation.data?.data ? (
          <div className="flex items-center gap-2 text-xs">
            <IntegrityBadge status={exportMutation.data.data.status} />
            <span className="text-slate-500">
              {exportMutation.data.data.package_checksum?.slice(0, 16) ?? "—"}
            </span>
          </div>
        ) : null}

        {exportsQuery.isLoading ? (
          <LoadingState label="Loading exports" />
        ) : exportsQuery.isError ? (
          <ErrorState
            description="Unable to load export history."
            title="Exports unavailable"
          />
        ) : !exportsQuery.data?.data.items.length ? (
          <EmptyState
            description="No packages have been exported for this case yet."
            title="No exports"
          />
        ) : (
          <ul className="space-y-2 text-xs text-slate-400">
            {exportsQuery.data.data.items.map((item) => (
              <li
                className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-800 px-3 py-2"
                key={item.id}
              >
                <button
                  className="text-left text-slate-200 hover:text-cyan-300"
                  onClick={() => onSelectExport?.(item.id)}
                  type="button"
                >
                  {item.format} · {new Date(item.created_at).toLocaleString()}
                </button>
                <div className="flex items-center gap-2">
                  <IntegrityBadge status={item.status} />
                  {item.status === "COMPLETED" ? (
                    <Button
                      onClick={async () => {
                        const blob =
                          await interoperabilityApi.downloadExport(item.id);
                        const url = URL.createObjectURL(blob);
                        const anchor = document.createElement("a");
                        anchor.href = url;
                        anchor.download = `export-${item.id}.zip`;
                        anchor.click();
                        URL.revokeObjectURL(url);
                      }}
                      size="sm"
                      variant="secondary"
                    >
                      <Download size={14} /> Download
                    </Button>
                  ) : null}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </Panel>
  );
}
