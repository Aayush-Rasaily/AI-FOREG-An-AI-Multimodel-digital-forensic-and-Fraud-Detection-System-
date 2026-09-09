import { memo } from "react";
import {
  FileArchive,
  FileBarChart,
  GitBranch,
  GitMerge,
  Clock3,
  ScanSearch,
} from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";

interface InvestigationSummaryCardsProps {
  evidenceAnalyzed: number;
  modalitiesAvailable: number;
  fusionCompleted: number;
  correlationCompleted: number;
  timelineGenerated: number;
  reportsAvailable: number;
}

const items = [
  {
    key: "evidence",
    label: "Evidence analyzed",
    icon: FileArchive,
    field: "evidenceAnalyzed" as const,
  },
  {
    key: "modalities",
    label: "Modalities available",
    icon: ScanSearch,
    field: "modalitiesAvailable" as const,
  },
  {
    key: "fusion",
    label: "Fusion completed",
    icon: GitMerge,
    field: "fusionCompleted" as const,
  },
  {
    key: "correlation",
    label: "Correlation completed",
    icon: GitBranch,
    field: "correlationCompleted" as const,
  },
  {
    key: "timeline",
    label: "Timeline generated",
    icon: Clock3,
    field: "timelineGenerated" as const,
  },
  {
    key: "reports",
    label: "Reports available",
    icon: FileBarChart,
    field: "reportsAvailable" as const,
  },
];

function InvestigationSummaryCardsComponent(
  props: InvestigationSummaryCardsProps,
) {
  return (
    <Card className="min-w-0 duration-fast transition-shadow hover:shadow-md">
      <CardHeader>
        <div>
          <CardTitle>Investigation summary</CardTitle>
          <p className="mt-1 text-caption text-muted">
            Executive coverage across forensic pipelines
          </p>
        </div>
      </CardHeader>
      <CardContent>
        <ul className="grid grid-cols-1 gap-2 sm:grid-cols-2 xl:grid-cols-3">
          {items.map((item) => {
            const Icon = item.icon;
            return (
              <li
                className="flex items-center gap-3 rounded-lg border border-border bg-background/40 p-3"
                key={item.key}
              >
                <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-soft text-primary">
                  <Icon aria-hidden="true" size={16} />
                </span>
                <div>
                  <p className="text-micro uppercase tracking-wider text-subtle">
                    {item.label}
                  </p>
                  <p className="text-lg font-semibold text-foreground">
                    {props[item.field]}
                  </p>
                </div>
              </li>
            );
          })}
        </ul>
      </CardContent>
    </Card>
  );
}

export const InvestigationSummaryCards = memo(
  InvestigationSummaryCardsComponent,
);
