import { cn } from "../../lib/utils";

export function ProgressIndicator({
  value,
  label,
}: {
  value: number;
  label?: string;
}) {
  const clamped = Math.max(0, Math.min(100, Math.round(value)));
  return (
    <div className="w-full">
      {label && (
        <div className="mb-1 flex justify-between text-caption text-muted">
          <span>{label}</span>
          <span>{clamped}%</span>
        </div>
      )}
      <div className="h-2 overflow-hidden rounded-full bg-surface-muted">
        <div
          aria-valuemax={100}
          aria-valuemin={0}
          aria-valuenow={clamped}
          className={cn("h-full rounded-full bg-primary")}
          role="progressbar"
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
}
