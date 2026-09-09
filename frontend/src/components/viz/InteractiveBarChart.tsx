import { Download, ImageDown } from "lucide-react";
import { useRef, useState } from "react";

import { exportSvgAsPng, exportSvgAsSvg } from "../../lib/chartExport";
import { cn } from "../../lib/utils";
import { Button } from "../ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";
import { VIZ_TONE_FILL, type VizSlice } from "./types";

interface InteractiveBarChartProps {
  title: string;
  description?: string;
  slices: VizSlice[];
  selectedId?: string | null;
  onSelect?: (slice: VizSlice | null) => void;
  emptyLabel?: string;
  exportName?: string;
  allowZoom?: boolean;
}

export function InteractiveBarChart({
  title,
  description,
  slices,
  selectedId,
  onSelect,
  emptyLabel = "No data yet",
  exportName = "chart",
  allowZoom = true,
}: InteractiveBarChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [hoverId, setHoverId] = useState<string | null>(null);
  const [zoom, setZoom] = useState(1);
  const max = Math.max(1, ...slices.map((s) => s.value));
  const width = 640;
  const height = 220;
  const pad = { top: 16, right: 16, bottom: 48, left: 40 };
  const innerW = width - pad.left - pad.right;
  const innerH = height - pad.top - pad.bottom;
  const barGap = 8;
  const barW =
    slices.length === 0
      ? 0
      : Math.max(8, (innerW - barGap * (slices.length - 1)) / slices.length);
  const hovered = slices.find((s) => s.id === hoverId);

  return (
    <Card className="min-w-0">
      <CardHeader className="flex-col items-start gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <CardTitle>{title}</CardTitle>
          {description && (
            <p className="mt-1 text-caption text-muted">{description}</p>
          )}
        </div>
        <div className="flex flex-wrap gap-1">
          {allowZoom && (
            <>
              <Button
                aria-label="Zoom out chart"
                onClick={() => setZoom((z) => Math.max(0.5, Number((z - 0.25).toFixed(2))))}
                size="sm"
                type="button"
                variant="ghost"
              >
                −
              </Button>
              <Button
                aria-label="Zoom in chart"
                onClick={() => setZoom((z) => Math.min(3, Number((z + 0.25).toFixed(2))))}
                size="sm"
                type="button"
                variant="ghost"
              >
                +
              </Button>
            </>
          )}
          <Button
            aria-label={`Export ${title} as SVG`}
            onClick={() => {
              if (svgRef.current) {
                exportSvgAsSvg(svgRef.current, `${exportName}.svg`);
              }
            }}
            size="sm"
            type="button"
            variant="secondary"
          >
            <Download aria-hidden="true" size={14} />
            SVG
          </Button>
          <Button
            aria-label={`Export ${title} as PNG`}
            onClick={() => {
              if (svgRef.current) {
                void exportSvgAsPng(svgRef.current, `${exportName}.png`);
              }
            }}
            size="sm"
            type="button"
            variant="secondary"
          >
            <ImageDown aria-hidden="true" size={14} />
            PNG
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {slices.length === 0 ? (
          <p className="py-10 text-center text-caption text-muted">{emptyLabel}</p>
        ) : (
          <div className="relative overflow-x-auto">
            <svg
              aria-label={title}
              className="h-auto w-full min-w-[280px]"
              height={height}
              ref={svgRef}
              role="img"
              viewBox={`0 0 ${width} ${height}`}
            >
              {[0, 0.25, 0.5, 0.75, 1].map((t) => {
                const y = pad.top + innerH * (1 - t);
                return (
                  <g key={t}>
                    <line
                      stroke="var(--color-border, #e2e8f0)"
                      strokeDasharray="3 3"
                      x1={pad.left}
                      x2={width - pad.right}
                      y1={y}
                      y2={y}
                    />
                    <text
                      fill="var(--color-muted, #64748b)"
                      fontSize="10"
                      textAnchor="end"
                      x={pad.left - 6}
                      y={y + 3}
                    >
                      {Math.round((max / zoom) * t)}
                    </text>
                  </g>
                );
              })}
              {slices.map((slice, index) => {
                const x = pad.left + index * (barW + barGap);
                const scaled = Math.min(slice.value * zoom, max);
                const barH = (scaled / max) * innerH;
                const y = pad.top + innerH - barH;
                const active =
                  selectedId === slice.id || hoverId === slice.id;
                return (
                  <g key={slice.id}>
                    <rect
                      aria-label={`${slice.label}: ${slice.value}`}
                      className="cursor-pointer duration-fast transition-opacity"
                      fill={VIZ_TONE_FILL[slice.tone ?? "primary"]}
                      height={Math.max(2, barH)}
                      opacity={
                        selectedId && selectedId !== slice.id ? 0.35 : active ? 1 : 0.85
                      }
                      onClick={() =>
                        onSelect?.(
                          selectedId === slice.id ? null : slice,
                        )
                      }
                      onKeyDown={(event) => {
                        if (event.key === "Enter" || event.key === " ") {
                          event.preventDefault();
                          onSelect?.(
                            selectedId === slice.id ? null : slice,
                          );
                        }
                      }}
                      onMouseEnter={() => setHoverId(slice.id)}
                      onMouseLeave={() => setHoverId(null)}
                      role="button"
                      rx={4}
                      tabIndex={0}
                      width={barW}
                      x={x}
                      y={y}
                    />
                    <text
                      fill="var(--color-muted, #64748b)"
                      fontSize="10"
                      textAnchor="middle"
                      transform={`rotate(-28 ${x + barW / 2} ${height - 10})`}
                      x={x + barW / 2}
                      y={height - 10}
                    >
                      {slice.label.length > 12
                        ? `${slice.label.slice(0, 11)}…`
                        : slice.label}
                    </text>
                  </g>
                );
              })}
            </svg>
            {hovered && (
              <div
                aria-live="polite"
                className="pointer-events-none absolute right-3 top-3 rounded-lg border border-border bg-surface px-3 py-2 text-caption shadow-md"
                role="tooltip"
              >
                <p className="font-medium text-foreground">{hovered.label}</p>
                <p className="text-muted">
                  {hovered.value}
                  {hovered.meta ? ` · ${hovered.meta}` : ""}
                </p>
                <p className="mt-1 text-micro text-subtle">Click to filter</p>
              </div>
            )}
            <ul
              aria-label={`${title} legend`}
              className="mt-3 flex flex-wrap gap-2"
            >
              {slices.map((slice) => (
                <li key={slice.id}>
                  <button
                    className={cn(
                      "inline-flex items-center gap-1.5 rounded-pill border border-border px-2 py-1 text-micro text-muted hover:text-foreground",
                      selectedId === slice.id && "border-primary text-primary",
                    )}
                    onClick={() =>
                      onSelect?.(selectedId === slice.id ? null : slice)
                    }
                    type="button"
                  >
                    <span
                      aria-hidden="true"
                      className="h-2 w-2 rounded-full"
                      style={{
                        background: VIZ_TONE_FILL[slice.tone ?? "primary"],
                      }}
                    />
                    {slice.label} ({slice.value})
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
