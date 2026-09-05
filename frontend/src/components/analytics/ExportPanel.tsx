import { Button } from "../ui/Button";
import { Panel } from "../ui/Panel";

interface ExportPanelProps {
  onExport: () => void;
  exporting?: boolean;
  lastExport?: string | null;
}

export function ExportPanel({
  onExport,
  exporting,
  lastExport,
}: ExportPanelProps) {
  return (
    <Panel
      description="Export the latest analytics snapshot as JSON."
      title="Export Panel"
    >
      <div className="space-y-3 p-4">
        <Button disabled={exporting} onClick={onExport} size="sm">
          Export JSON
        </Button>
        {lastExport ? (
          <p className="text-xs text-slate-500">Last export: {lastExport}</p>
        ) : (
          <p className="text-xs text-slate-500">No export yet.</p>
        )}
      </div>
    </Panel>
  );
}
