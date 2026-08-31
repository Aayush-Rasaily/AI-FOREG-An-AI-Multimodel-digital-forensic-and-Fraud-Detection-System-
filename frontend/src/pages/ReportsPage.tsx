import { FileBarChart, FileText } from "lucide-react";

import { PageHeader } from "../components/layout/PageHeader";
import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";

export function ReportsPage() {
  return (
    <div>
      <PageHeader
        description="Reviewable, provenance-aware reports generated from completed investigations."
        eyebrow="Reporting"
        title="Reports"
      />
      <Card>
        <EmptyState
          description="Report generation is not connected. Reports will appear only after an investigation and its evidence-backed findings are available."
          icon={<FileBarChart aria-hidden="true" size={20} />}
          title="No reports available"
        />
      </Card>
      <div className="mt-4 flex items-center gap-2 text-xs text-slate-600">
        <FileText aria-hidden="true" size={14} />
        Report provenance and export controls are reserved for a later phase.
      </div>
    </div>
  );
}

