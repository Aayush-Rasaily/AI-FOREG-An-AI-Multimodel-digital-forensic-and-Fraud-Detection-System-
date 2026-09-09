import {
  useId,
  useState,
  type HTMLAttributes,
  type ReactNode,
} from "react";
import { ChevronDown } from "lucide-react";

import { cn } from "../../lib/utils";

interface PanelProps extends HTMLAttributes<HTMLElement> {
  title?: string;
  description?: string;
  /** When true, header toggles body visibility while keeping DOM (scroll) intact. */
  collapsible?: boolean;
  defaultCollapsed?: boolean;
  headerActions?: ReactNode;
}

export function Panel({
  className,
  title,
  description,
  children,
  collapsible,
  defaultCollapsed = false,
  headerActions,
  ...props
}: PanelProps) {
  const [collapsed, setCollapsed] = useState(defaultCollapsed);
  const panelId = useId();
  const bodyId = `${panelId}-body`;
  const isCollapsible = collapsible ?? Boolean(title);
  const showHeader = Boolean(
    title || description || headerActions || isCollapsible,
  );

  return (
    <section
      className={cn(
        "rounded-xl border border-border bg-surface shadow-panel duration-normal transition-shadow",
        "hover:shadow-md",
        className,
      )}
      {...props}
    >
      {showHeader && (
        <div className="flex items-start gap-2 border-b border-border px-4 py-3">
          <div className="min-w-0 flex-1">
            {title && (
              <h2 className="text-caption font-semibold text-foreground">{title}</h2>
            )}
            {description && (
              <p className="mt-1 text-caption leading-relaxed text-muted">
                {description}
              </p>
            )}
          </div>
          {headerActions}
          {isCollapsible && (
            <button
              aria-controls={bodyId}
              aria-expanded={!collapsed}
              aria-label={collapsed ? "Expand panel" : "Collapse panel"}
              className={cn(
                "inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-muted",
                "hover:bg-surface-muted hover:text-foreground",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                "duration-fast transition-colors",
              )}
              onClick={() => setCollapsed((current) => !current)}
              type="button"
            >
              <ChevronDown
                aria-hidden="true"
                className={cn(
                  "duration-normal transition-transform",
                  collapsed && "-rotate-90",
                )}
                size={16}
              />
            </button>
          )}
        </div>
      )}
      <div
        className={cn(
          "grid duration-normal transition-[grid-template-rows]",
          collapsed ? "grid-rows-[0fr]" : "grid-rows-[1fr]",
        )}
        id={bodyId}
      >
        <div
          className={cn(
            "min-h-0",
            collapsed ? "overflow-hidden" : "overflow-auto",
          )}
        >
          {children}
        </div>
      </div>
    </section>
  );
}
