import { CheckCircle2, CircleDashed, TriangleAlert } from "lucide-react";

import { cn } from "../../lib/utils";

type StatusTone = "online" | "pending" | "warning" | "offline";

interface StatusIndicatorProps {
  label: string;
  tone: StatusTone;
  className?: string;
}

const toneStyles: Record<StatusTone, string> = {
  online: "text-success",
  pending: "text-warning",
  warning: "text-warning",
  offline: "text-subtle",
};

export function StatusIndicator({
  label,
  tone,
  className,
}: StatusIndicatorProps) {
  const Icon =
    tone === "online"
      ? CheckCircle2
      : tone === "offline"
        ? CircleDashed
        : TriangleAlert;

  return (
    <span className={cn("inline-flex items-center gap-2 text-caption", toneStyles[tone], className)}>
      <Icon aria-hidden="true" size={14} />
      <span>{label}</span>
    </span>
  );
}
