import { useRef, useState } from "react";
import type { CSSProperties, ReactNode, UIEvent } from "react";

type VirtualListProps<T> = {
  items: T[];
  rowHeight?: number;
  height?: number;
  overscan?: number;
  getKey: (item: T, index: number) => string;
  renderRow: (item: T, index: number) => ReactNode;
};

/** Lightweight windowed list for large collections (no extra dependency). */
export function VirtualList<T>({
  items,
  rowHeight = 88,
  height = 560,
  overscan = 6,
  getKey,
  renderRow,
}: VirtualListProps<T>) {
  const [scrollTop, setScrollTop] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  if (items.length <= 40) {
    return (
      <div className="divide-y divide-slate-800">
        {items.map((item, index) => (
          <div key={getKey(item, index)}>{renderRow(item, index)}</div>
        ))}
      </div>
    );
  }

  const start = Math.max(0, Math.floor(scrollTop / rowHeight) - overscan);
  const visibleCount = Math.ceil(height / rowHeight) + overscan * 2;
  const end = Math.min(items.length, start + visibleCount);
  const offsetY = start * rowHeight;
  const totalHeight = items.length * rowHeight;

  const onScroll = (event: UIEvent<HTMLDivElement>) => {
    setScrollTop(event.currentTarget.scrollTop);
  };

  const windowStyle: CSSProperties = {
    height: totalHeight,
    position: "relative",
  };
  const sliceStyle: CSSProperties = {
    position: "absolute",
    top: offsetY,
    left: 0,
    right: 0,
  };

  return (
    <div
      className="overflow-auto"
      onScroll={onScroll}
      ref={containerRef}
      style={{ height }}
    >
      <div style={windowStyle}>
        <div className="divide-y divide-slate-800" style={sliceStyle}>
          {items.slice(start, end).map((item, offset) => {
            const index = start + offset;
            return <div key={getKey(item, index)}>{renderRow(item, index)}</div>;
          })}
        </div>
      </div>
    </div>
  );
}
