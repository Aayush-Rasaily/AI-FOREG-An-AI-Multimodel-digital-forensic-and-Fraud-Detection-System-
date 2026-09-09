import { memo } from "react";
import { Link } from "react-router-dom";
import { ArrowUpRight } from "lucide-react";

import type { RecentCaseRow } from "../../hooks/useExecutiveDashboard";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";

function priorityTone(
  priority: RecentCaseRow["priority"],
): "success" | "info" | "warning" | "error" {
  if (priority === "CRITICAL") return "error";
  if (priority === "HIGH") return "warning";
  if (priority === "MEDIUM") return "info";
  return "success";
}

function RecentCasesWidgetComponent({ cases }: { cases: RecentCaseRow[] }) {
  return (
    <Card className="min-w-0 duration-fast transition-shadow hover:shadow-md">
      <CardHeader>
        <div>
          <CardTitle>Recent cases</CardTitle>
          <p className="mt-1 text-caption text-muted">
            Status, risk priority, and quick open
          </p>
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        {cases.length === 0 ? (
          <p className="py-6 text-center text-caption text-muted">
            No cases in the registry yet.
          </p>
        ) : (
          <ul aria-label="Recent cases" className="space-y-2">
            {cases.map((item) => (
              <li
                className="flex flex-col gap-2 rounded-lg border border-border bg-background/40 p-3 sm:flex-row sm:items-center sm:justify-between"
                key={item.id}
              >
                <div className="min-w-0">
                  <p className="truncate text-caption font-medium text-foreground">
                    {item.caseNumber} · {item.title}
                  </p>
                  <div className="mt-1 flex flex-wrap gap-1.5">
                    <Badge tone="neutral">
                      {item.status.replaceAll("_", " ")}
                    </Badge>
                    <Badge tone={priorityTone(item.priority)}>
                      Risk {item.priority}
                    </Badge>
                    <Badge tone="neutral">
                      Evidence{" "}
                      {item.evidenceCount == null ? "—" : item.evidenceCount}
                    </Badge>
                    <span className="text-micro text-subtle">
                      Updated {new Date(item.updatedAt).toLocaleString()}
                    </span>
                  </div>
                </div>
                <Link to={`/investigations/${item.id}`}>
                  <Button
                    aria-label={`Open ${item.caseNumber}`}
                    className="w-full sm:w-auto"
                    size="sm"
                    variant="secondary"
                  >
                    Open
                    <ArrowUpRight aria-hidden="true" size={14} />
                  </Button>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

export const RecentCasesWidget = memo(RecentCasesWidgetComponent);
