import type { InputHTMLAttributes } from "react";

import { cn } from "../../lib/utils";

interface SwitchProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "type"> {
  label?: string;
}

export function Switch({ className, label, id, checked, ...props }: SwitchProps) {
  return (
    <label className="inline-flex items-center gap-2 text-body" htmlFor={id}>
      <span
        className={cn(
          "relative inline-flex h-5 w-9 shrink-0 items-center rounded-full border border-border",
          checked ? "bg-primary" : "bg-surface-muted",
          className,
        )}
      >
        <input
          checked={checked}
          className="peer sr-only"
          id={id}
          role="switch"
          type="checkbox"
          {...props}
        />
        <span
          className={cn(
            "ml-0.5 h-4 w-4 rounded-full bg-foreground transition-transform",
            checked && "translate-x-4 bg-primary-foreground",
          )}
        />
      </span>
      {label && <span className="text-foreground">{label}</span>}
    </label>
  );
}
