import { X } from "lucide-react";
import type { ButtonHTMLAttributes } from "react";

import { cn } from "../../lib/utils";

interface FilterChipProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  active?: boolean;
  onClear?: () => void;
}

export function FilterChip({
  active = false,
  onClear,
  className,
  children,
  type = "button",
  ...props
}: FilterChipProps) {
  return (
    <button
      aria-pressed={active}
      className={cn(
        "inline-flex min-h-9 items-center gap-1.5 rounded-pill border px-3 text-caption font-medium duration-fast transition-colors",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        active
          ? "border-primary/40 bg-primary-soft text-primary"
          : "border-border bg-surface text-muted hover:bg-surface-muted hover:text-foreground",
        className,
      )}
      type={type}
      {...props}
    >
      <span>{children}</span>
      {active && onClear ? (
        <span
          aria-label="Clear filter"
          className="rounded-full p-0.5 hover:bg-primary/20"
          onClick={(event) => {
            event.stopPropagation();
            onClear();
          }}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              event.stopPropagation();
              onClear();
            }
          }}
          role="button"
          tabIndex={0}
        >
          <X aria-hidden="true" size={12} />
        </span>
      ) : null}
    </button>
  );
}
