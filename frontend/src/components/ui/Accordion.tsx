import type { ReactNode } from "react";

import { cn } from "../../lib/utils";

interface AccordionItem {
  id: string;
  title: string;
  content: ReactNode;
}

interface AccordionProps {
  items: AccordionItem[];
  className?: string;
}

export function Accordion({ items, className }: AccordionProps) {
  return (
    <div className={cn("divide-y divide-border rounded-md border border-border", className)}>
      {items.map((item) => (
        <details className="group p-0" key={item.id}>
          <summary className="cursor-pointer list-none px-4 py-3 text-display-h4 text-foreground hover:bg-surface-muted [&::-webkit-details-marker]:hidden">
            {item.title}
          </summary>
          <div className="text-caption px-4 pb-4 text-muted">{item.content}</div>
        </details>
      ))}
    </div>
  );
}
