import { FileAudio, FileImage, FileSignature, FileText, Film, File } from "lucide-react";

import type { EvidenceKind } from "../../types/investigation";
import { Badge } from "../ui/Badge";
import { Card } from "../ui/Card";

interface EvidenceCardProps {
  name: string;
  kind: EvidenceKind;
  meta?: string;
  selected?: boolean;
  onClick?: () => void;
}

const icons = {
  image: FileImage,
  pdf: FileText,
  video: Film,
  audio: FileAudio,
  document: FileText,
  signature: FileSignature,
};

export function EvidenceCard({
  name,
  kind,
  meta = "Awaiting evidence",
  selected = false,
  onClick,
}: EvidenceCardProps) {
  const Icon = icons[kind] || File;
  const content = (
    <>
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-800 text-slate-400">
        <Icon aria-hidden="true" size={17} strokeWidth={1.7} />
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate text-xs font-medium text-slate-200">{name}</p>
        <p className="mt-1 truncate text-[11px] text-slate-600">{meta}</p>
      </div>
      <Badge tone="neutral">{kind}</Badge>
    </>
  );

  if (onClick) {
    return (
      <button
        className={`flex w-full items-center gap-3 rounded-lg border p-3 text-left transition-colors ${
          selected
            ? "border-cyan-400/40 bg-cyan-400/10"
            : "border-slate-800 bg-slate-950/40 hover:border-slate-700 hover:bg-slate-900"
        }`}
        onClick={onClick}
        type="button"
      >
        {content}
      </button>
    );
  }

  return <Card className="flex items-center gap-3 p-3">{content}</Card>;
}

