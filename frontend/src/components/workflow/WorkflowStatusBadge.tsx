import type { InvestigationStatus } from "../../types/workflow";
import { Badge } from "../ui/Badge";

const tones: Record<
  InvestigationStatus,
  "neutral" | "primary" | "success" | "warning" | "error" | "info"
> = {
  NEW: "neutral",
  ACTIVE: "primary",
  UNDER_REVIEW: "warning",
  REQUIRES_CHANGES: "error",
  APPROVED: "success",
  REPORTED: "info",
  ARCHIVED: "neutral",
};

export function WorkflowStatusBadge({
  status,
}: {
  status: InvestigationStatus | string;
}) {
  const tone = tones[status as InvestigationStatus] ?? "neutral";
  return <Badge tone={tone}>{status.replaceAll("_", " ")}</Badge>;
}
