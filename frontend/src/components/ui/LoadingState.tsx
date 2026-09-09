import { LoaderCircle } from "lucide-react";

export function LoadingState({
  label = "Loading workspace",
}: {
  label?: string;
}) {
  return (
    <div
      aria-busy="true"
      aria-live="polite"
      className="flex min-h-48 flex-col items-center justify-center gap-3 text-muted animate-fade-in"
      role="status"
    >
      <LoaderCircle
        aria-hidden="true"
        className="animate-spin text-primary"
        size={22}
      />
      <span className="text-caption">{label}</span>
    </div>
  );
}
