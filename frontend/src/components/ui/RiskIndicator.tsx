import { cn } from "../../lib/utils";

type RiskLevel = "low" | "medium" | "high" | "critical" | "unknown";

const styles: Record<RiskLevel, string> = {
  low: "bg-success/15 text-success",
  medium: "bg-warning/15 text-warning",
  high: "bg-danger/15 text-danger",
  critical: "bg-danger text-primary-foreground",
  unknown: "bg-surface-muted text-muted",
};

export function RiskIndicator({
  level,
  label,
}: {
  level: RiskLevel;
  label?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-caption font-medium",
        styles[level],
      )}
    >
      {label ?? level}
    </span>
  );
}
