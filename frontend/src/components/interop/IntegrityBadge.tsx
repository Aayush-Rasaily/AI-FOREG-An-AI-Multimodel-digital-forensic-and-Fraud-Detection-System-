import { Badge } from "../ui/Badge";

function tone(
  status: string,
): "success" | "warning" | "error" | "neutral" {
  const value = status.toUpperCase();
  if (
    value === "VALID" ||
    value === "COMPLETED" ||
    value === "PASSED" ||
    value === "PASS"
  ) {
    return "success";
  }
  if (
    value === "DEGRADED" ||
    value === "WARN" ||
    value === "CONFLICTS" ||
    value === "PARTIAL"
  ) {
    return "warning";
  }
  if (
    value === "INVALID" ||
    value === "FAILED" ||
    value === "FAIL"
  ) {
    return "error";
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
