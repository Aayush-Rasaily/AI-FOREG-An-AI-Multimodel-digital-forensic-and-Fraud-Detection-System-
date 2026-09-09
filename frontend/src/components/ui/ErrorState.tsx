import { AlertCircle } from "lucide-react";

import { Button } from "./Button";

interface ErrorStateProps {
  title?: string;
  description?: string;
  onRetry?: () => void;
}

export function ErrorState({
  title = "Workspace unavailable",
  description = "The requested information could not be loaded.",
  onRetry,
}: ErrorStateProps) {
  return (
    <div
      className="flex min-h-48 flex-col items-center justify-center px-6 text-center animate-fade-in"
      role="alert"
    >
      <AlertCircle aria-hidden="true" className="text-warning" size={22} />
      <h3 className="mt-3 text-body font-medium text-foreground">{title}</h3>
      <p className="mt-2 max-w-md text-caption leading-relaxed text-muted">
        {description}
      </p>
      {onRetry && (
        <Button className="mt-5" onClick={onRetry} size="sm" variant="secondary">
          Try again
        </Button>
      )}
    </div>
  );
}
