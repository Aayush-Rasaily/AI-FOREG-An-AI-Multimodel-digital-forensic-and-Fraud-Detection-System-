import { memo } from "react";
import {
  FileAudio,
  FileImage,
  FileSignature,
  FileText,
  Film,
  File,
} from "lucide-react";

import type { EvidenceKind } from "../../types/investigation";
import { cn } from "../../lib/utils";
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

function EvidenceCardComponent({
  name,
  kind,
  meta = "Awaiting evidence",
  selected = false,
  onClick,
}: EvidenceCardProps) {
  const Icon = icons[kind] || File;
  const content = (
    <>
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-surface-muted text-muted sm:h-9 sm:w-9">
        <Icon aria-hidden="true" size={17} strokeWidth={1.7} />
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate text-caption font-medium text-foreground sm:text-xs">
          {name}
        </p>
        <p className="mt-1 truncate text-[11px] text-subtle">{meta}</p>
      </div>
      <Badge className="shrink-0" tone="neutral">
        {kind}
      </Badge>
    </>
  );

  if (onClick) {
    return (
      <button
        className={cn(
          "flex w-full min-h-14 items-center gap-3 rounded-lg border p-3 text-left duration-fast transition-colors",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
          selected
            ? "border-primary/40 bg-primary/10"
            : "border-border bg-background/40 hover:border-border-strong hover:bg-background-offset",
        )}
        onClick={onClick}
        type="button"
      >
        {content}
      </button>
    );
  }

  return (
    <Card className="flex min-h-14 items-center gap-3 p-3 duration-fast transition-shadow hover:shadow-md">
      {content}
    </Card>
  );
}

export const EvidenceCard = memo(EvidenceCardComponent);
