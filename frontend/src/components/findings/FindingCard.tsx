import { CircleAlert, Info, ShieldAlert } from "lucide-react";

import type { Finding } from "../../types/investigation";
import { Badge } from "../ui/Badge";
import { ConfidenceIndicator } from "../ui/ConfidenceIndicator";
import { Card } from "../ui/Card";

interface FindingCardProps {
  finding?: Finding;
}

const stateLabels = {
  confirmed: "Confirmed indicator",
  "strong-suspicion": "Strong suspicion",
  suspicious: "Suspicious",
  informational: "Informational",
};

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
              Finding cards will render engine-backed observations here. No forensic conclusion is shown.
            </p>
          </div>
        </div>
      </Card>
    );
  }

  const icon = finding.severity === "critical" || finding.severity === "high" ? ShieldAlert : CircleAlert;
  const Icon = icon;

  return (
    <Card className="p-4">
      <div className="flex items-start gap-3">
        <Icon aria-hidden="true" className="mt-0.5 text-amber-300" size={17} />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-xs font-medium text-slate-200">{finding.type}</p>
            <Badge tone={finding.severity === "critical" ? "red" : "amber"}>
              {stateLabels[finding.state]}
            </Badge>
          </div>
          <p className="mt-2 text-xs leading-relaxed text-slate-400">{finding.description}</p>
          <div className="mt-3 flex flex-wrap gap-x-4 gap-y-2">
            <ConfidenceIndicator value={finding.confidence} />
            {finding.engine && <span className="text-[11px] text-slate-600">Engine: {finding.engine}</span>}
            {finding.location && <span className="text-[11px] text-slate-600">Location: {finding.location}</span>}
            {finding.evidenceSource && (
              <span className="text-[11px] text-slate-600">
                Source: {finding.evidenceSource}
              </span>
            )}
            {finding.timestamp && (
              <time className="text-[11px] text-slate-600" dateTime={finding.timestamp}>
                {finding.timestamp}
              </time>
            )}
            {finding.supportingEvidence && (
              <span className="text-[11px] text-slate-600">
                {finding.supportingEvidence.length} supporting items
              </span>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}

