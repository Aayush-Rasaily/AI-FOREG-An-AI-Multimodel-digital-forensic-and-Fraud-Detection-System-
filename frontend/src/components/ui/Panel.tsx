import type { HTMLAttributes } from "react";

import { cn } from "../../lib/utils";

interface PanelProps extends HTMLAttributes<HTMLElement> {
  title?: string;
  description?: string;
}

export function Panel({
  className,
  title,
  description,
  children,
  ...props
}: PanelProps) {
  return (
    <section
      className={cn(
        "rounded-xl border border-slate-800 bg-slate-950/35 shadow-panel",
        className,
      )}
      {...props}
    >
      {(title || description) && (
        <div className="border-b border-slate-800 px-4 py-3">
          {title && <h2 className="text-xs font-semibold text-slate-200">{title}</h2>}
          {description && (
            <p className="mt-1 text-xs leading-relaxed text-slate-500">{description}</p>
          )}
        </div>
      )}
      {children}
    </section>
  );
}

