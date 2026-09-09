import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { useProductivity } from "../../context/ProductivityContext";
import { cn } from "../../lib/utils";

interface ResizableSplitProps {
  storageKey: string;
  left: ReactNode;
  right: ReactNode;
  defaultLeftPercent?: number;
  minLeftPercent?: number;
  maxLeftPercent?: number;
  className?: string;
}

export function ResizableSplit({
  storageKey,
  left,
  right,
  defaultLeftPercent = 32,
  minLeftPercent = 18,
  maxLeftPercent = 70,
  className,
}: ResizableSplitProps) {
  const { panelSizes, setPanelSize } = useProductivity();
  const [percent, setPercent] = useState(
    () => panelSizes[storageKey] ?? defaultLeftPercent,
  );
  const dragging = useRef(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (panelSizes[storageKey] != null) {
      setPercent(panelSizes[storageKey]);
    }
  }, [panelSizes, storageKey]);

  const onMove = useCallback(
    (clientX: number) => {
      const rect = containerRef.current?.getBoundingClientRect();
      if (!rect) {
        return;
      }
      const next = ((clientX - rect.left) / rect.width) * 100;
      const clamped = Math.min(
        maxLeftPercent,
        Math.max(minLeftPercent, next),
      );
      setPercent(clamped);
    },
    [maxLeftPercent, minLeftPercent],
  );

  useEffect(() => {
    const onPointerMove = (event: PointerEvent) => {
      if (!dragging.current) {
        return;
      }
      onMove(event.clientX);
    };
    const onPointerUp = () => {
      if (!dragging.current) {
        return;
      }
      dragging.current = false;
      setPanelSize(storageKey, percent);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", onPointerUp);
    return () => {
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerup", onPointerUp);
    };
  }, [onMove, percent, setPanelSize, storageKey]);

  return (
    <div
      className={cn(
        "hidden min-h-[24rem] md:flex md:items-stretch",
        className,
      )}
      ref={containerRef}
    >
      <div className="min-w-0" style={{ width: `${percent}%` }}>
        {left}
      </div>
      <button
        aria-label="Resize panels"
        className="group relative mx-1 w-2 shrink-0 cursor-col-resize rounded-pill bg-border hover:bg-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        onPointerDown={(event) => {
          event.preventDefault();
          dragging.current = true;
          document.body.style.cursor = "col-resize";
          document.body.style.userSelect = "none";
        }}
        type="button"
      >
        <span className="absolute inset-y-0 -left-1 -right-1" />
      </button>
      <div className="min-w-0 flex-1">{right}</div>
    </div>
  );
}
