import { Activity, Database, ServerCog } from "lucide-react";

import { PageHeader } from "../components/layout/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { ErrorState } from "../components/ui/ErrorState";
import { LoadingState } from "../components/ui/LoadingState";
import { StatusIndicator } from "../components/ui/StatusIndicator";
import { useHealthQuery, useSystemInfoQuery } from "../hooks/useHealth";

export function SystemPage() {
  const healthQuery = useHealthQuery();
  const systemInfoQuery = useSystemInfoQuery();

  return (
    <div>
      <PageHeader
        description="Safe operational signals for the application boundary. Secrets and infrastructure paths are never displayed."
        eyebrow="Operations"
        title="System"
      />
      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Service health</CardTitle>
            <Activity aria-hidden="true" className="text-subtle" size={17} />
          </CardHeader>
          <CardContent>
            {healthQuery.isPending && <LoadingState label="Checking API health" />}
            {healthQuery.isError && (
              <ErrorState
                description="The health service could not be reached."
                onRetry={() => void healthQuery.refetch()}
              />
            )}
            {healthQuery.data && (
              <div className="space-y-3">
                <div className="flex items-center justify-between rounded-lg border border-border bg-background/50 p-3">
                  <span className="text-xs text-muted">Application</span>
                  <StatusIndicator
                    label={healthQuery.data.data.status}
                    tone={healthQuery.data.data.status === "healthy" ? "online" : "warning"}
                  />
                </div>
                <div className="flex items-center justify-between rounded-lg border border-border bg-background/50 p-3">
                  <span className="text-xs text-muted">Database</span>
                  <StatusIndicator
                    label={healthQuery.data.data.database}
                    tone={healthQuery.data.data.database === "healthy" ? "online" : "warning"}
                  />
                </div>
              </div>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Runtime information</CardTitle>
            <ServerCog aria-hidden="true" className="text-subtle" size={17} />
          </CardHeader>
          <CardContent>
            {systemInfoQuery.isPending && <LoadingState label="Loading runtime information" />}
            {systemInfoQuery.isError && (
              <ErrorState
                description="Runtime information is temporarily unavailable."
                onRetry={() => void systemInfoQuery.refetch()}
              />
            )}
            {systemInfoQuery.data && (
              <dl className="divide-y divide-border">
                <div className="flex justify-between gap-4 py-3 text-xs">
                  <dt className="text-subtle">Service</dt>
                  <dd className="text-right text-muted">{systemInfoQuery.data.data.service}</dd>
                </div>
                <div className="flex justify-between gap-4 py-3 text-xs">
                  <dt className="text-subtle">Version</dt>
                  <dd className="text-right text-muted">{systemInfoQuery.data.data.version}</dd>
                </div>
                <div className="flex justify-between gap-4 py-3 text-xs">
                  <dt className="text-subtle">Runtime</dt>
                  <dd className="text-right text-muted">{systemInfoQuery.data.data.python_version}</dd>
                </div>
                <div className="flex justify-between gap-4 py-3 text-xs">
                  <dt className="text-subtle">Platform</dt>
                  <dd className="text-right text-muted">{systemInfoQuery.data.data.platform}</dd>
                </div>
              </dl>
            )}
          </CardContent>
        </Card>
      </div>
      <div className="mt-4 flex items-center gap-2 text-xs text-subtle">
        <Database aria-hidden="true" size={14} />
        Operational details are sourced from the configured API only.
      </div>
    </div>
  );
}

