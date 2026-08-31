import {
  Activity,
  AlertTriangle,
  BarChart3,
  FileArchive,
  FolderSearch,
} from "lucide-react";

import { StatCard } from "../components/dashboard/StatCard";
import { SystemStatusCard } from "../components/dashboard/SystemStatusCard";
import { PageHeader } from "../components/layout/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { NetworkErrorState } from "../components/ui/NetworkErrorState";
import { StatusIndicator } from "../components/ui/StatusIndicator";
import { useHealthQuery } from "../hooks/useHealth";

export function DashboardPage() {
  const healthQuery = useHealthQuery();

  return (
    <div>
      <PageHeader
        description="A controlled workspace for evidence-led investigations and accountable analysis."
        eyebrow="Operations overview"
        title="Investigation dashboard"
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard detail="No connected case data" icon={FolderSearch} label="Active investigations" value="0" />
        <StatCard detail="Evidence index not connected" icon={FileArchive} label="Evidence items" value="0" />
        <StatCard detail="Analysis pipeline pending" icon={BarChart3} label="Analyses completed" value="0" />
        <StatCard detail="Findings engine not connected" icon={AlertTriangle} label="Suspicious findings" value="0" />
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-[1.35fr_1fr]">
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Recent investigations</CardTitle>
              <p className="mt-1 text-xs text-slate-500">Cases requiring attention will appear here.</p>
            </div>
            <StatusIndicator label="No records" tone="offline" />
          </CardHeader>
          <CardContent>
            <EmptyState
              className="min-h-56 rounded-lg border border-dashed border-slate-800"
              description="Investigation records will populate after the case service is connected. No sample cases are shown."
              icon={<FolderSearch aria-hidden="true" size={20} />}
              title="No investigations yet"
            />
          </CardContent>
        </Card>
        <SystemStatusCard />
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Recent evidence</CardTitle>
              <p className="mt-1 text-xs text-slate-500">Chain-of-custody activity will be shown here.</p>
            </div>
            <FileArchive aria-hidden="true" className="text-slate-600" size={17} />
          </CardHeader>
          <CardContent>
            <EmptyState
              description="Evidence ingestion is reserved for a later phase. This workspace never fabricates evidence."
              icon={<FileArchive aria-hidden="true" size={20} />}
              title="Evidence index is empty"
            />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Analysis activity</CardTitle>
              <p className="mt-1 text-xs text-slate-500">Queued and completed work will appear here.</p>
            </div>
            <Activity aria-hidden="true" className="text-slate-600" size={17} />
          </CardHeader>
          <CardContent>
            {healthQuery.isError ? (
              <NetworkErrorState onRetry={() => void healthQuery.refetch()} />
            ) : (
              <EmptyState
                description="No analysis jobs are available. Connect the orchestration service to monitor activity."
                icon={<Activity aria-hidden="true" size={20} />}
                title="No analysis activity"
              />
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

