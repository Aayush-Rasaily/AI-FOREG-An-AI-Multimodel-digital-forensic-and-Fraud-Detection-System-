import type { InvestigationStatus } from "../../types/workflow";
import { Badge } from "../ui/Badge";

const tones: Record<
  InvestigationStatus,
  "neutral" | "cyan" | "green" | "amber" | "red" | "purple"
> = {
  NEW: "neutral",
  ACTIVE: "cyan",
  UNDER_REVIEW: "amber",
  REQUIRES_CHANGES: "red",
  APPROVED: "green",
  REPORTED: "purple",
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
