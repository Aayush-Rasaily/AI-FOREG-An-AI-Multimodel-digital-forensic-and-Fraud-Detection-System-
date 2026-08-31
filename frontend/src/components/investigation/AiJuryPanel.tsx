import {
  AudioLines,
  BrainCircuit,
  FileSignature,
  Gavel,
  Image,
  ScanText,
} from "lucide-react";

import { Badge } from "../ui/Badge";
import { Panel } from "../ui/Panel";

const specialists = [
  { label: "Forensic Evidence Analyst", icon: BrainCircuit },
  { label: "Document / Image Specialist", icon: Image },
  { label: "Multimedia Specialist", icon: AudioLines },
  { label: "Signature Specialist", icon: FileSignature },
  { label: "Consistency Analyst", icon: ScanText },
  { label: "Senior Forensic Judge", icon: Gavel },
];

export function AiJuryPanel() {
  return (
    <Panel
      description="A future multi-agent review surface with explicit provenance and dissent visibility."
      title="AI Jury"
    >
      <div className="grid gap-2 p-4 sm:grid-cols-2">
        {specialists.map(({ icon: Icon, label }) => (
          <div
            className="flex items-center gap-3 rounded-lg border border-slate-800 bg-slate-950/50 p-3"
            key={label}
          >
            <Icon aria-hidden="true" className="shrink-0 text-slate-600" size={16} />
            <span className="min-w-0 flex-1 text-xs text-slate-400">{label}</span>
            <Badge tone="neutral">Not connected</Badge>
          </div>
        ))}
      </div>
      <div className="border-t border-slate-800 px-4 py-3">
        <p className="text-[11px] text-slate-600">
          Analysis engine not connected. No votes, confidence, or verdicts are available.
        </p>
      </div>
    </Panel>
  );
}

