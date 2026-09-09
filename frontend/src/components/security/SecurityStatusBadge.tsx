import type { ComplianceStatus } from "../../types/security";
import { Badge } from "../ui/Badge";

const tones: Record<
  ComplianceStatus,
  "success" | "warning" | "error" | "neutral"
> = {
  COMPLIANT: "success",
  PARTIAL: "warning",
  NON_COMPLIANT: "error",
};

export function SecurityStatusBadge({
  status,
}: {
  status: ComplianceStatus | string;
}) {
  const tone = tones[status as ComplianceStatus] ?? "neutral";
  return <Badge tone={tone}>{status.replaceAll("_", " ")}</Badge>;
}
