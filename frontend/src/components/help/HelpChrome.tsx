import { useState } from "react";
import { CircleHelp, Keyboard } from "lucide-react";

import { Button } from "../ui/Button";
import { Dialog } from "../ui/Dialog";

const SHORTCUTS: Array<{ keys: string; action: string }> = [
  { keys: "Ctrl / ⌘ + K", action: "Open command palette" },
  { keys: "?", action: "Open keyboard shortcuts (when focused in shell)" },
  { keys: "Esc", action: "Close dialogs, drawers, and palettes" },
  { keys: "Tab / Shift+Tab", action: "Move focus between controls" },
  { keys: "Enter / Space", action: "Activate focused buttons and filters" },
];

export function KeyboardShortcutsHelp({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  return (
    <Dialog
      description="Common shortcuts for investigators and supervisors."
      onClose={onClose}
      open={open}
      title="Keyboard shortcuts"
    >
      <ul className="space-y-2" aria-label="Keyboard shortcuts">
        {SHORTCUTS.map((item) => (
          <li
            className="flex items-center justify-between gap-3 rounded-lg border border-border bg-background/40 px-3 py-2"
            key={item.keys}
          >
            <span className="text-caption text-muted">{item.action}</span>
            <kbd className="rounded-md border border-border bg-surface-muted px-2 py-1 font-mono text-micro text-foreground">
              {item.keys}
            </kbd>
          </li>
        ))}
      </ul>
    </Dialog>
  );
}

export function HelpMenuButton() {
  const [open, setOpen] = useState(false);
  return (
    <>
      <Button
        aria-label="Open keyboard shortcuts help"
        onClick={() => setOpen(true)}
        size="sm"
        type="button"
        variant="ghost"
      >
        <Keyboard aria-hidden="true" size={16} />
        <span className="hidden lg:inline">Shortcuts</span>
      </Button>
      <KeyboardShortcutsHelp onClose={() => setOpen(false)} open={open} />
    </>
  );
}

export function ContextualHelp({
  title,
  body,
}: {
  title: string;
  body: string;
}) {
  return (
    <details className="group rounded-lg border border-border bg-surface-muted/40 p-3">
      <summary className="flex cursor-pointer list-none items-center gap-2 text-caption font-medium text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
        <CircleHelp aria-hidden="true" className="text-primary" size={14} />
        {title}
      </summary>
      <p className="mt-2 text-caption leading-relaxed text-muted">{body}</p>
    </details>
  );
}
