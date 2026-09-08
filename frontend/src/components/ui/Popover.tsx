import type { ReactNode } from "react";

import { cn } from "../../lib/utils";

interface PopoverProps {
  label: string;
  children: ReactNode;
  className?: string;
}

export function Popover({ label, children, className }: PopoverProps) {
  return (
    <details className={cn("relative inline-block", className)}>
      <summary className="cursor-pointer list-none rounded-md px-2 py-1 text-caption text-muted hover:bg-surface-muted hover:text-foreground [&::-webkit-details-marker]:hidden">
        {label}
      </summary>
      <div className="absolute z-30 mt-2 min-w-48 rounded-md border border-border bg-surface p-3 shadow-md">
        {children}
      </div>
    </details>
  );
}
