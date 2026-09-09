import { ShieldCheck } from "lucide-react";

interface ConfidenceIndicatorProps {
  value?: number;
  unavailable?: boolean;
}

export function ConfidenceIndicator({
  value,
  unavailable = false,
}: ConfidenceIndicatorProps) {
  if (unavailable || value === undefined) {
    return (
      <span className="inline-flex items-center gap-1.5 text-caption text-subtle">
        <ShieldCheck aria-hidden="true" size={13} />
        Not available
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1.5 text-caption text-muted">
      <ShieldCheck aria-hidden="true" size={13} />
      {Math.round(value * 100)}% confidence
    </span>
  );
}
