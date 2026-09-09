import { useSystemStorageQuery } from "../../hooks/useSystem";
import { Badge } from "../ui/Badge";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

export function StoragePanel() {
  const query = useSystemStorageQuery();
  const data = query.data?.data;

  return (
    <Panel
      description="Storage backend utilization."
      title="Storage"
    >
      <div className="p-4">
        {query.isLoading && <LoadingState label="Loading storage…" />}
        {query.isError && (
          <ErrorState
            description="Storage stats unavailable."
            onRetry={() => void query.refetch()}
            title="Storage failed"
          />
        )}
        {data && (
          <div className="space-y-3">
            <Badge tone="neutral">{data.backend} backend</Badge>
            <dl className="divide-y divide-border text-xs">
              <div className="flex justify-between py-2">
                <dt className="text-muted">Used</dt>
                <dd className="text-foreground">{data.used_mb} MB</dd>
              </div>
              <div className="flex justify-between py-2">
                <dt className="text-muted">Disk usage</dt>
                <dd className="text-foreground">
                  {data.disk_percent != null
                    ? `${data.disk_percent}%`
                    : "—"}
                </dd>
              </div>
              <div className="flex justify-between py-2">
                <dt className="text-muted">Max upload</dt>
                <dd className="text-foreground">
                  {data.max_upload_size_mb} MB
                </dd>
              </div>
            </dl>
          </div>
        )}
      </div>
    </Panel>
  );
}
