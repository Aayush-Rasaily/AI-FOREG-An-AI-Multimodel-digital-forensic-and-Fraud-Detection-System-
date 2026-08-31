import type { SelectHTMLAttributes } from "react";

import { cn } from "../../lib/utils";

export function Select({
  className,
  ...props
}: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={cn(
        "h-10 rounded-lg border border-slate-700 bg-slate-950 px-3 text-sm text-slate-300",
        "focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/20",
        className,
      )}
      {...props}
    />
  );
}

