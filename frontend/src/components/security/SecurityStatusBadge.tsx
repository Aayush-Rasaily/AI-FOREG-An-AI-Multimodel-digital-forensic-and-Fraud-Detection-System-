import type { ComplianceStatus } from "../../types/security";
import { Badge } from "../ui/Badge";

const tones: Record<
  ComplianceStatus,
  "green" | "amber" | "red" | "neutral"
> = {
  COMPLIANT: "green",
  PARTIAL: "amber",
  NON_COMPLIANT: "red",
};

export function SecurityStatusBadge({
  status,
}: {
  status: ComplianceStatus | string;
}) {
  const tone = tones[status as ComplianceStatus] ?? "neutral";
  return <Badge tone={tone}>{status.replaceAll("_", " ")}</Badge>;
}
