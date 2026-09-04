import { Badge } from "../ui/Badge";

function tone(
  status: string,
): "green" | "amber" | "red" | "neutral" {
  const value = status.toUpperCase();
  if (
    value === "VALID" ||
    value === "COMPLETED" ||
    value === "PASSED" ||
    value === "PASS"
  ) {
    return "green";
  }
  if (
    value === "DEGRADED" ||
    value === "WARN" ||
    value === "CONFLICTS" ||
    value === "PARTIAL"
  ) {
    return "amber";
  }
  if (
    value === "INVALID" ||
    value === "FAILED" ||
    value === "FAIL"
  ) {
    return "red";
  }
  return "neutral";
}

interface IntegrityBadgeProps {
  status: string;
  label?: string;
}

export function IntegrityBadge({ status, label }: IntegrityBadgeProps) {
  return (
    <Badge tone={tone(status)}>
      {label ? `${label}: ${status}` : status}
    </Badge>
  );
}
