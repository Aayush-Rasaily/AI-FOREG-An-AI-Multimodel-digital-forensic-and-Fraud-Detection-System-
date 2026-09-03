import { RefreshCw } from "lucide-react";

import { DiagnosticsPanel } from "../components/system/DiagnosticsPanel";
import { HealthPanel } from "../components/system/HealthPanel";
import { JobsPanel } from "../components/system/JobsPanel";
import { MetricsPanel } from "../components/system/MetricsPanel";
import { StoragePanel } from "../components/system/StoragePanel";
import { PageHeader } from "../components/layout/PageHeader";
import { Button } from "../components/ui/Button";
import { useRefreshSystemDashboard } from "../hooks/useSystem";

export function SystemDashboardPage() {
  const refresh = useRefreshSystemDashboard();

  return (
    <div>
      <PageHeader
        actions={
          <Button onClick={refresh} size="sm" variant="secondary">
            <RefreshCw size={14} /> Refresh
          </Button>
        }
        description="Enterprise operational monitoring for AI-Forge administrators."
        eyebrow="Administration"
        title="System Dashboard"
      />
      <div className="space-y-4">
        <HealthPanel />
        <div className="grid gap-4 xl:grid-cols-2">
          <MetricsPanel />
          <JobsPanel />
        </div>
        <div className="grid gap-4 xl:grid-cols-2">
          <StoragePanel />
          <DiagnosticsPanel />
        </div>
      </div>
    </div>
  );
}
