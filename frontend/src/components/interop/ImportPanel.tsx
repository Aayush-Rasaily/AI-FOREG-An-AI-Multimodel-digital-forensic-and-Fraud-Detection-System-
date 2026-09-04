import { useRef } from "react";
import { Upload } from "lucide-react";

import {
  useImportPackageMutation,
  useImportsQuery,
} from "../../hooks/useInteroperability";
import { IntegrityBadge } from "./IntegrityBadge";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

export function ImportPanel() {
  const inputRef = useRef<HTMLInputElement>(null);
  const importsQuery = useImportsQuery();
  const importMutation = useImportPackageMutation();

  return (
    <Panel
      description="Validate investigation packages. Existing cases are never overwritten automatically."
      title="Import"
    >
      <div className="space-y-4 p-4">
        <input
          accept=".zip,application/zip"
          className="hidden"
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) {
              importMutation.mutate(file);
            }
          }}
          ref={inputRef}
          type="file"
        />
        <Button
          disabled={importMutation.isPending}
          onClick={() => inputRef.current?.click()}
          size="sm"
          variant="secondary"
        >
          <Upload size={14} /> Validate package
        </Button>

        {importMutation.isError ? (
          <ErrorState
            description="Import validation request failed."
            title="Import error"
          />
        ) : null}
        {importMutation.data?.data ? (
          <div className="space-y-2 text-xs text-slate-400">
            <IntegrityBadge
              label="Integrity"
              status={importMutation.data.data.integrity_status}
            />
            {importMutation.data.data.conflicts.length ? (
              <p className="text-amber-300">
                Conflicts: {importMutation.data.data.conflicts.join(", ")}
              </p>
            ) : null}
          </div>
        ) : null}

        {importsQuery.isLoading ? (
          <LoadingState label="Loading imports" />
        ) : importsQuery.isError ? (
          <ErrorState
            description="Unable to load import history."
            title="Imports unavailable"
          />
        ) : !importsQuery.data?.data.items.length ? (
          <EmptyState
            description="No import validation jobs have been recorded yet."
            title="No imports"
          />
        ) : (
          <ul className="space-y-2 text-xs text-slate-400">
            {importsQuery.data.data.items.map((item) => (
              <li
                className="flex items-center justify-between gap-2 rounded-lg border border-slate-800 px-3 py-2"
                key={item.id}
              >
                <span className="text-slate-200">
                  {item.source_filename ?? item.id}
                </span>
                <IntegrityBadge status={item.integrity_status} />
              </li>
            ))}
          </ul>
        )}
      </div>
    </Panel>
  );
}
