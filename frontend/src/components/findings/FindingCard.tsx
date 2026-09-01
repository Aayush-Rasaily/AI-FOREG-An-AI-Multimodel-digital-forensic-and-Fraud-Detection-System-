import { CircleAlert, Info, ShieldAlert } from "lucide-react";

import type { ForensicFinding } from "../../types/forensics";
import { Badge } from "../ui/Badge";
import { ConfidenceIndicator } from "../ui/ConfidenceIndicator";
import { Card } from "../ui/Card";

interface FindingCardProps {
  finding?: ForensicFinding;
}

export function FindingCard({ finding }: FindingCardProps) {
  if (!finding) {
    return (
      <Card className="p-4">
        <div className="flex items-start gap-3">
          <div className="rounded-lg bg-slate-800 p-2 text-slate-500">
            <Info aria-hidden="true" size={16} />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-300">No finding recorded</p>
            <p className="mt-1 text-[11px] leading-relaxed text-slate-600">
              Finding cards render engine-backed forensic observations. No
              authenticity verdict is shown.
            </p>
          </div>
        </div>
      </Card>
    );
  }

  const Icon =
    finding.severity === "CRITICAL" || finding.severity === "HIGH"
      ? ShieldAlert
      : CircleAlert;

  return (
    <Card className="p-4">
      <div className="flex items-start gap-3">
        <Icon aria-hidden="true" className="mt-0.5 text-amber-300" size={17} />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-xs font-medium text-slate-200">{finding.category}</p>
            <Badge tone={finding.severity === "CRITICAL" ? "red" : "amber"}>
              {finding.severity}
            </Badge>
            <Badge tone="neutral">{finding.detector}</Badge>
          </div>
          <p className="mt-2 text-xs leading-relaxed text-slate-400">
            {finding.description}
          </p>
          <p className="mt-2 text-xs leading-relaxed text-slate-500">
            {finding.explanation}
          </p>
          {finding.recommendation && (
            <p className="mt-2 text-[11px] text-cyan-400/80">
              {finding.recommendation}
            </p>
          )}
          <div className="mt-3 flex flex-wrap gap-x-4 gap-y-2">
            <ConfidenceIndicator value={finding.confidence} />
            <time className="text-[11px] text-slate-600" dateTime={finding.created_at}>
              {finding.created_at}
            </time>
          </div>
        </div>
      </div>
    </Card>
  );
}
