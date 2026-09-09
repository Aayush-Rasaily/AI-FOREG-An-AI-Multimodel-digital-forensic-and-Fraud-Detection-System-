import type { ReactNode } from "react";

import { FileSearch } from "lucide-react";

import { cn } from "../../lib/utils";

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: ReactNode;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({
  title,
  description,
  icon,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex min-h-48 flex-col items-center justify-center px-6 py-10 text-center animate-fade-in",
        className,
      )}
      role="status"
    >
      <div className="mb-4 rounded-xl border border-border bg-surface-muted p-3 text-subtle">
        {icon || <FileSearch aria-hidden="true" size={20} />}
      </div>
      <h3 className="text-body font-medium text-foreground">{title}</h3>
      <p className="mt-2 max-w-md text-caption leading-relaxed text-muted">
        {description}
      </p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}
