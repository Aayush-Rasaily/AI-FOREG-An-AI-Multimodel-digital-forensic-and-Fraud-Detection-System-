import { useState } from "react";

import { ExportPanel } from "../components/interop/ExportPanel";
import { ImportPanel } from "../components/interop/ImportPanel";
import { ManifestViewer } from "../components/interop/ManifestViewer";
import { PackageHistoryPanel } from "../components/interop/PackageHistoryPanel";
import { PageHeader } from "../components/layout/PageHeader";

export function InteroperabilityPage() {
  const [selectedExportId, setSelectedExportId] = useState<string | null>(null);

  return (
    <div>
      <PageHeader
        description="Import and export investigation packages with deterministic manifests and integrity checks."
        eyebrow="Administration"
        title="Interoperability"
      />
      <div className="space-y-4">
        <div className="grid gap-4 xl:grid-cols-2">
          <ImportPanel />
          <PackageHistoryPanel onSelectExport={setSelectedExportId} />
        </div>
        <ManifestViewer exportId={selectedExportId} />
      </div>
    </div>
  );
}

interface CaseInteropSectionProps {
  caseId: string;
}

export function CaseInteropSection({ caseId }: CaseInteropSectionProps) {
  const [selectedExportId, setSelectedExportId] = useState<string | null>(null);

  return (
    <div className="space-y-4">
      <ExportPanel caseId={caseId} onSelectExport={setSelectedExportId} />
      <div className="grid gap-4 xl:grid-cols-2">
        <PackageHistoryPanel
          caseId={caseId}
          onSelectExport={setSelectedExportId}
        />
        <ManifestViewer exportId={selectedExportId} />
      </div>
    </div>
  );
}
