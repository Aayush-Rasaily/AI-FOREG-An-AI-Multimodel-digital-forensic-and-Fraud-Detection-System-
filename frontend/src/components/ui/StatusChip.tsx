import { cn } from "../../lib/utils";
import { Badge, type BadgeTone } from "./Badge";

type ChipStatus = "success" | "warning" | "error" | "info" | "neutral";

const map: Record<ChipStatus, BadgeTone> = {
  success: "success",
  warning: "warning",
  error: "error",
  info: "info",
  neutral: "neutral",
};

export function StatusChip({
  status,
  children,
  className,
}: {
  status: ChipStatus;
  children: string;
  className?: string;
}) {
  return (
    <Badge className={cn("uppercase tracking-wide", className)} tone={map[status]}>
      {children}
    </Badge>
  );
}
