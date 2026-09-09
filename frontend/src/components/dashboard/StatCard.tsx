import { memo, type ComponentType } from "react";
import { ArrowDownRight, ArrowRight, ArrowUpRight } from "lucide-react";

import { cn } from "../../lib/utils";
import { Card } from "../ui/Card";

interface StatCardProps {
  label: string;
  value: string;
  detail: string;
  icon: ComponentType<{ size?: number; strokeWidth?: number }>;
  trend?: string;
  tone?: "up" | "down" | "flat";
}

function StatCardComponent({
  label,
  value,
  detail,
  icon: Icon,
  trend,
  tone = "flat",
}: StatCardProps) {
  const TrendIcon =
    tone === "up" ? ArrowUpRight : tone === "down" ? ArrowDownRight : ArrowRight;

  return (
    <Card className="p-4 duration-fast transition-shadow hover:shadow-md sm:p-5">
      <div className="flex items-start justify-between">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-border bg-background text-primary sm:h-9 sm:w-9">
          <Icon aria-hidden="true" size={17} strokeWidth={1.7} />
        </div>
        <TrendIcon
          aria-hidden="true"
          className={cn(
            "text-muted",
            tone === "up" && "text-success",
            tone === "down" && "text-danger",
          )}
          size={16}
        />
      </div>
      <p className="mt-4 text-xs text-muted sm:mt-5">{label}</p>
      <p className="mt-1 text-xl font-semibold tracking-tight text-foreground sm:text-2xl">
        {value}
      </p>
      <p className="mt-1 text-[11px] text-subtle">{detail}</p>
      {trend && (
        <p
          className={cn(
            "mt-2 text-micro",
            tone === "up" && "text-success",
            tone === "down" && "text-danger",
            tone === "flat" && "text-subtle",
          )}
        >
          {trend}
        </p>
      )}
    </Card>
  );
}

export const StatCard = memo(StatCardComponent);
