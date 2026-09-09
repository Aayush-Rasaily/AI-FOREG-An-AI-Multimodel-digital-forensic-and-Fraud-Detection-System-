import type { ReactNode } from "react";

import { cn } from "../../lib/utils";

export function PageContainer({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("mx-auto w-full max-w-[1800px]", className)}>
      {children}
    </div>
  );
}

export function SectionHeader({
  title,
  description,
}: {
  title: string;
  description?: string;
}) {
  return (
    <div className="mb-4">
      <h2 className="text-display-h2 text-foreground">{title}</h2>
      {description && (
        <p className="mt-1 text-caption text-muted">{description}</p>
      )}
    </div>
  );
}
