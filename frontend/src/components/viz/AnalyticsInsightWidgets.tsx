import { memo, type ReactNode } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle,
  FileBarChart,
  GitBranch,
  GitMerge,
  Clock3,
  Flame,
} from "lucide-react";

import { Badge } from "../ui/Badge";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";

export interface InsightItem {
  id: string;
  title: string;
  detail: string;
  href?: string;
  tone?: "neutral" | "warning" | "error" | "success" | "info" | "primary";
}

interface WidgetProps {
  title: string;
  description?: string;
  items: InsightItem[];
  icon?: ReactNode;
  empty?: string;
}

function InsightWidgetComponent({
  title,
  description,
  items,
  icon,
  empty = "No items yet",
}: WidgetProps) {
  return (
    <Card className="min-w-0">
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <div>
            <CardTitle>{title}</CardTitle>
            {description && (
              <p className="mt-1 text-caption text-muted">{description}</p>
            )}
          </div>
          {icon}
        </div>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <p className="py-4 text-center text-caption text-muted">{empty}</p>
        ) : (
          <ul className="space-y-2" aria-label={title}>
            {items.map((item) => (
              <li
                className="rounded-lg border border-border bg-background/40 px-3 py-2"
                key={item.id}
              >
                <div className="flex items-start justify-between gap-2">
                  {item.href ? (
                    <Link
                      className="text-caption font-medium text-primary hover:underline"
                      to={item.href}
                    >
                      {item.title}
                    </Link>
                  ) : (
                    <p className="text-caption font-medium text-foreground">
                      {item.title}
                    </p>
                  )}
                  {item.tone && <Badge tone={item.tone}>{item.tone}</Badge>}
                </div>
                <p className="mt-1 text-caption text-muted">{item.detail}</p>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

export const InsightWidget = memo(InsightWidgetComponent);

interface AnalyticsInsightWidgetsProps {
  topRisks: InsightItem[];
  latestFindings: InsightItem[];
  recentReports: InsightItem[];
  recentCorrelations: InsightItem[];
  fusionSummary: InsightItem[];
  timelineSummary: InsightItem[];
  mostActiveCases: InsightItem[];
}

export function AnalyticsInsightWidgets(props: AnalyticsInsightWidgetsProps) {
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
      <InsightWidget
        description="Elevated case priorities"
        empty="No elevated risks"
        icon={<Flame aria-hidden="true" className="text-warning" size={16} />}
        items={props.topRisks}
        title="Top risks"
      />
      <InsightWidget
        description="Integrity and analytics alerts"
        empty="No findings"
        icon={
          <AlertTriangle aria-hidden="true" className="text-danger" size={16} />
        }
        items={props.latestFindings}
        title="Latest findings"
      />
      <InsightWidget
        description="Report registry signals"
        empty="No reports"
        icon={
          <FileBarChart aria-hidden="true" className="text-primary" size={16} />
        }
        items={props.recentReports}
        title="Recent reports"
      />
      <InsightWidget
        description="Correlation engine signals"
        empty="No correlations"
        icon={
          <GitBranch aria-hidden="true" className="text-success" size={16} />
        }
        items={props.recentCorrelations}
        title="Recent correlations"
      />
      <InsightWidget
        description="Cross-modal fusion"
        empty="No fusion runs"
        icon={<GitMerge aria-hidden="true" className="text-warning" size={16} />}
        items={props.fusionSummary}
        title="Fusion summary"
      />
      <InsightWidget
        description="Timeline reconstructions"
        empty="No timeline signals"
        icon={<Clock3 aria-hidden="true" className="text-info" size={16} />}
        items={props.timelineSummary}
        title="Timeline summary"
      />
      <InsightWidget
        description="Recently updated investigations"
        empty="No active cases"
        icon={<Flame aria-hidden="true" className="text-primary" size={16} />}
        items={props.mostActiveCases}
        title="Most active cases"
      />
    </div>
  );
}
