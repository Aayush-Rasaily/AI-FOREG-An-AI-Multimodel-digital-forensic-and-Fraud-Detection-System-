import { RefreshCw } from "lucide-react";

import { ConfigurationPanel } from "../components/deployment/ConfigurationPanel";
import { DeploymentPanel } from "../components/deployment/DeploymentPanel";
import { HealthOverview } from "../components/deployment/HealthOverview";
import { ReleasePanel } from "../components/deployment/ReleasePanel";
import { PageHeader } from "../components/layout/PageHeader";
import { Button } from "../components/ui/Button";
import { useRefreshSystemStatus } from "../hooks/useSystemStatus";

export function SystemStatusPage() {
  const refresh = useRefreshSystemStatus();

  return (
    <div>
      <PageHeader
        actions={
          <Button onClick={refresh} size="sm" variant="secondary">
            <RefreshCw size={14} /> Refresh
          </Button>
        }
        description="Production readiness, release identity, and operational validation."
        eyebrow="Administration"
        title="Deployment Status"
      />
      <div className="space-y-4">
        <HealthOverview />
        <div className="grid gap-4 xl:grid-cols-2">
          <DeploymentPanel />
          <ReleasePanel />
        </div>
        <ConfigurationPanel />
      </div>
    </div>
  );
}
