import type { InputHTMLAttributes } from "react";

import { cn } from "../../lib/utils";

interface CheckboxProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "type"> {
  label?: string;
}

export function Checkbox({ className, label, id, ...props }: CheckboxProps) {
  return (
    <label className="inline-flex items-center gap-2 text-body text-foreground" htmlFor={id}>
      <input
        className={cn(
          "h-4 w-4 rounded-sm border-border text-primary focus:ring-ring",
          className,
        )}
        id={id}
        type="checkbox"
        {...props}
      />
      {label && <span>{label}</span>}
    </label>
  );
}
