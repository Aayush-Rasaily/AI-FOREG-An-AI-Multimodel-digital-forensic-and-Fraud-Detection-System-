import { IntegrityBadge } from "./IntegrityBadge";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";
import { useExportManifestQuery } from "../../hooks/useInteroperability";

interface ManifestViewerProps {
  exportId: string | null;
}

export function ManifestViewer({ exportId }: ManifestViewerProps) {
  const query = useExportManifestQuery(exportId);

  if (!exportId) {
    return (
      <Panel description="Select an export to inspect its manifest." title="Manifest">
        <EmptyState
          description="Choose a completed export from package history."
          title="No manifest selected"
        />
      </Panel>
    );
  }

  if (query.isLoading) {
    return <LoadingState label="Loading manifest" />;
  }
  if (query.isError) {
    return (
      <ErrorState
        description="Unable to load package manifest."
        title="Manifest unavailable"
      />
    );
  }

  const data = query.data?.data;
  if (!data) {
    return (
      <EmptyState
        description="Manifest payload was empty."
        title="No manifest"
      />
    );
  }

  const files = Array.isArray(data.manifest.files)
    ? (data.manifest.files as { path?: string; sha256?: string }[])
    : [];

  return (
    <Panel
      description="Deterministic package manifest with per-file SHA-256 digests."
      title="Manifest"
    >
      <div className="space-y-3 p-4 text-xs text-slate-400">
        <div className="flex flex-wrap gap-2">
          <IntegrityBadge status="VALID" label="Manifest" />
          <span className="font-mono text-slate-300">
            {data.manifest_checksum.slice(0, 16)}…
          </span>
        </div>
        <p>
          Package checksum:{" "}
          <span className="font-mono text-slate-200">
            {data.package_checksum}
          </span>
        </p>
        <p>
          Schema: {String(data.manifest.schema_version ?? "—")} · Evidence:{" "}
          {String(data.manifest.evidence_count ?? 0)} · Reports:{" "}
          {String(data.manifest.report_count ?? 0)}
        </p>
        {files.length ? (
          <ul className="max-h-48 space-y-1 overflow-y-auto">
            {files.map((file) => (
              <li key={file.path}>
                <span className="text-slate-300">{file.path}</span>:{" "}
                <span className="font-mono">{file.sha256?.slice(0, 12)}…</span>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState
            description="Manifest lists no member files."
            title="No files"
          />
        )}
      </div>
    </Panel>
  );
}
