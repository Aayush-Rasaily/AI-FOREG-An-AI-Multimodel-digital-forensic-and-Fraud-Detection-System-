import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { X } from "lucide-react";

import { cn } from "../../lib/utils";
import { Button } from "./Button";

type ToastTone = "info" | "success" | "warning" | "error";

interface ToastItem {
  id: string;
  title: string;
  description?: string;
  tone: ToastTone;
}

interface ToastContextValue {
  push: (toast: Omit<ToastItem, "id">) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

const toneClass: Record<ToastTone, string> = {
  info: "border-info/30 bg-surface text-foreground",
  success: "border-success/30 bg-surface text-foreground",
  warning: "border-warning/30 bg-surface text-foreground",
  error: "border-danger/30 bg-surface text-foreground",
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);

  const push = useCallback((toast: Omit<ToastItem, "id">) => {
    const id = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    setItems((current) => [...current, { ...toast, id }]);
    window.setTimeout(() => {
      setItems((current) => current.filter((item) => item.id !== id));
    }, 4000);
  }, []);

  const value = useMemo(() => ({ push }), [push]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div
        aria-live="polite"
        className="pointer-events-none fixed right-4 top-4 z-50 flex w-80 flex-col gap-2"
      >
        {items.map((item) => (
          <div
            className={cn(
              "pointer-events-auto animate-slide-in-right rounded-md border p-3 shadow-lg",
              toneClass[item.tone],
            )}
            key={item.id}
            role="status"
          >
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="text-display-h4">{item.title}</p>
                {item.description && (
                  <p className="text-caption mt-1 text-muted">{item.description}</p>
                )}
              </div>
              <Button
                aria-label="Dismiss notification"
                onClick={() =>
                  setItems((current) =>
                    current.filter((entry) => entry.id !== item.id),
                  )
                }
                size="sm"
                variant="ghost"
              >
                <X aria-hidden="true" size={14} />
              </Button>
            </div>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const value = useContext(ToastContext);
  if (!value) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return value;
}
