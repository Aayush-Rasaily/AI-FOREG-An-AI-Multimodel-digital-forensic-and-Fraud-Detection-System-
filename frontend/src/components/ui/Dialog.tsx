import { useEffect } from "react";
import type { ReactNode } from "react";
import { X } from "lucide-react";

import { Button } from "./Button";

interface DialogProps {
  open: boolean;
  title: string;
  description?: string;
  onClose: () => void;
  children: ReactNode;
}

export function Dialog({
  open,
  title,
  description,
  onClose,
  children,
}: DialogProps) {
  useEffect(() => {
    if (!open) {
      return;
    }
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose, open]);

  if (!open) {
    return null;
  }

  return (
    <div
      aria-labelledby="dialog-title"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm"
      onMouseDown={(event) => {
        if (event.currentTarget === event.target) {
          onClose();
        }
      }}
      role="dialog"
    >
      <div className="w-full max-w-lg rounded-xl border border-slate-700 bg-slate-900 shadow-2xl">
        <div className="flex items-start justify-between border-b border-slate-800 p-5">
          <div>
            <h2 className="text-base font-semibold text-slate-100" id="dialog-title">
              {title}
            </h2>
            {description && <p className="mt-1 text-xs text-slate-500">{description}</p>}
          </div>
          <Button aria-label="Close dialog" onClick={onClose} size="sm" variant="ghost">
            <X aria-hidden="true" size={16} />
          </Button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  );
}

