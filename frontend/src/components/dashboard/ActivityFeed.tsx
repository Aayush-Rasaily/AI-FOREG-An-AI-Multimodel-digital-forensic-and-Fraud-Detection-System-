import { memo } from "react";
import {
  Activity,
  FileArchive,
  FileBarChart,
  GitMerge,
  Layers3,
} from "lucide-react";

import type { ActivityItem } from "../../hooks/useExecutiveDashboard";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";

const icons = {
  case: Layers3,
  evidence: FileArchive,
  analysis: Activity,
  fusion: GitMerge,
  report: FileBarChart,
  timeline: Activity,
  system: Activity,
};

function ActivityFeedComponent({ items }: { items: ActivityItem[] }) {
  return (
    <Card className="min-w-0 duration-fast transition-shadow hover:shadow-md">
      <CardHeader>
        <div>
          <CardTitle>Recent activity</CardTitle>
          <p className="mt-1 text-caption text-muted">
            Newest first · derived from cases, analytics, and platform metrics
          </p>
        </div>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <p className="py-6 text-center text-caption text-muted">
            No activity signals yet. Open cases and refresh analytics to
            populate this feed.
          </p>
        ) : (
          <ol className="space-y-3" aria-label="Activity feed">
            {items.map((item) => {
              const Icon = icons[item.kind] ?? Activity;
              return (
                <li
                  className="flex min-h-11 items-start gap-3 rounded-lg border border-border bg-background/40 px-3 py-2.5"
                  key={item.id}
                >
                  <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-surface-muted text-primary">
                    <Icon aria-hidden="true" size={14} />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-caption font-medium text-foreground">
                      {item.title}
                    </p>
                    <p className="mt-0.5 text-caption text-muted">{item.detail}</p>
                    <p className="mt-1 text-micro text-subtle">
                      {new Date(item.at).toLocaleString()}
                    </p>
                  </div>
                </li>
              );
            })}
          </ol>
        )}
      </CardContent>
    </Card>
  );
}

export const ActivityFeed = memo(ActivityFeedComponent);
