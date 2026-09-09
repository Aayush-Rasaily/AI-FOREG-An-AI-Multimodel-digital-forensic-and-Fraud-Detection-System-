import type { ReactNode } from "react";
import { ChevronDown } from "lucide-react";

interface DropdownProps {
  label: string;
  children: ReactNode;
}

export function Dropdown({ label, children }: DropdownProps) {
  return (
    <details className="relative">
      <summary className="flex h-9 cursor-pointer list-none items-center gap-2 rounded-lg px-3 text-caption text-muted duration-fast transition-colors hover:bg-surface-muted hover:text-foreground [&::-webkit-details-marker]:hidden">
        {label}
        <ChevronDown aria-hidden="true" size={14} />
      </summary>
      <div className="absolute right-0 z-30 mt-2 min-w-40 rounded-lg border border-border bg-surface p-1 shadow-lg">
        {children}
      </div>
    </details>
  );
}
