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
        "flex min-h-48 flex-col items-center justify-center px-6 py-10 text-center",
        className,
      )}
    >
      <div className="mb-4 rounded-xl border border-slate-800 bg-slate-900 p-3 text-slate-500">
        {icon || <FileSearch aria-hidden="true" size={20} />}
      </div>
      <h3 className="text-sm font-medium text-slate-200">{title}</h3>
      <p className="mt-2 max-w-md text-xs leading-relaxed text-slate-500">
        {description}
      </p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

