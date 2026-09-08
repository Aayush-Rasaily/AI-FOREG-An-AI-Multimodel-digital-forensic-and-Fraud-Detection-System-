import { useEffect } from "react";
import type { ReactNode } from "react";
import { X } from "lucide-react";

import { cn } from "../../lib/utils";
import { Button } from "./Button";

interface DrawerProps {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
}

export function Drawer({ open, title, onClose, children }: DrawerProps) {
  useEffect(() => {
    if (!open) {
      return;
    }
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose, open]);

  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <button
        aria-label="Close drawer"
        className="absolute inset-0 bg-background/70"
        onClick={onClose}
        type="button"
      />
      <aside
        aria-labelledby="drawer-title"
        className={cn(
          "relative h-full w-full max-w-md border-l border-border bg-surface p-5 shadow-lg",
        )}
        role="dialog"
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-display-h2" id="drawer-title">
            {title}
          </h2>
          <Button aria-label="Close drawer" onClick={onClose} size="sm" variant="ghost">
            <X aria-hidden="true" size={16} />
          </Button>
        </div>
        {children}
      </aside>
    </div>
  );
}
