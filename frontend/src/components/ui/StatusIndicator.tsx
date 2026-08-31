import { CheckCircle2, CircleDashed, TriangleAlert } from "lucide-react";

import { cn } from "../../lib/utils";

type StatusTone = "online" | "pending" | "warning" | "offline";

interface StatusIndicatorProps {
  label: string;
  tone: StatusTone;
  className?: string;
}

const toneStyles: Record<StatusTone, string> = {
  online: "text-emerald-300",
  pending: "text-amber-300",
  warning: "text-amber-300",
  offline: "text-slate-500",
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
    <span className={cn("inline-flex items-center gap-2 text-xs", toneStyles[tone], className)}>
      <Icon aria-hidden="true" size={14} />
      <span>{label}</span>
    </span>
  );
}

