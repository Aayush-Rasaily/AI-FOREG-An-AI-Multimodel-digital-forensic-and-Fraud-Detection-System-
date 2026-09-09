import { Download, ImageDown } from "lucide-react";
import { useMemo, useRef, useState } from "react";

import { exportSvgAsPng, exportSvgAsSvg } from "../../lib/chartExport";
import type { TimelineEvent } from "../../types/timeline";
import { Button } from "../ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";

const TYPE_COLOR: Record<string, string> = {
  evidence: "#0891b2",
  fusion: "#d97706",
  correlation: "#16a34a",
  report: "#dc2626",
  ai: "#7c3aed",
  processing: "#2563eb",
  other: "#64748b",
};

function eventBucket(type: string): keyof typeof TYPE_COLOR {
  if (type.includes("fusion")) return "fusion";
  if (type.includes("correlation") || type.includes("intelligence")) {
    return "correlation";
  }
  if (type.includes("report")) return "report";
  if (type.includes("evidence") || type.includes("custody")) return "evidence";
  if (type.includes("ai") || type.includes("analysis")) return "ai";
  if (type.includes("processing") || type.includes("extraction")) {
    return "processing";
  }
  return "other";
}

interface InteractiveTimelineVizProps {
  events: TimelineEvent[];
  title?: string;
}

export function InteractiveTimelineViz({
  events,
  title = "Interactive timeline",
}: InteractiveTimelineVizProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [zoom, setZoom] = useState(1);
  const [hoverId, setHoverId] = useState<string | null>(null);

  const dated = useMemo(
    () =>
      events
        .filter((e) => e.normalized_timestamp)
        .map((e) => ({
          ...e,
          ts: new Date(e.normalized_timestamp as string).getTime(),
          bucket: eventBucket(e.event_type),
        }))
        .sort((a, b) => a.ts - b.ts),
    [events],
  );

  const width = 720;
  const height = 180;
  const pad = 28;
  const minTs = dated[0]?.ts ?? 0;
  const maxTs = dated[dated.length - 1]?.ts ?? 1;
  const span = Math.max(1, maxTs - minTs) / zoom;

  const hovered = dated.find((e) => e.event_id === hoverId);

  const groups = useMemo(() => {
    const map = new Map<string, number>();
    for (const event of dated) {
      map.set(event.bucket, (map.get(event.bucket) ?? 0) + 1);
    }
    return [...map.entries()];
  }, [dated]);

  return (
    <Card className="min-w-0">
      <CardHeader className="flex-col items-start gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <CardTitle>{title}</CardTitle>
          <p className="mt-1 text-caption text-muted">
            Color-coded markers · zoom · export
          </p>
        </div>
        <div className="flex flex-wrap gap-1">
          <Button
            aria-label="Zoom out timeline"
            onClick={() => setZoom((z) => Math.max(1, z - 0.5))}
            size="sm"
            type="button"
            variant="ghost"
          >
            −
          </Button>
          <Button
            aria-label="Zoom in timeline"
            onClick={() => setZoom((z) => Math.min(8, z + 0.5))}
            size="sm"
            type="button"
            variant="ghost"
          >
            +
          </Button>
          <Button
            aria-label="Export timeline SVG"
            onClick={() => {
              if (svgRef.current) exportSvgAsSvg(svgRef.current, "timeline.svg");
            }}
            size="sm"
            type="button"
            variant="secondary"
          >
            <Download aria-hidden="true" size={14} />
            SVG
          </Button>
          <Button
            aria-label="Export timeline PNG"
            onClick={() => {
              if (svgRef.current) void exportSvgAsPng(svgRef.current, "timeline.png");
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
        {dated.length === 0 ? (
          <p className="py-8 text-center text-caption text-muted">
            No timestamped events to plot
          </p>
        ) : (
          <div className="relative overflow-x-auto">
            <svg
              aria-label={title}
              className="h-auto w-full min-w-[320px]"
              height={height}
              ref={svgRef}
              role="img"
              viewBox={`0 0 ${width} ${height}`}
            >
              <line
                stroke="var(--color-border, #cbd5e1)"
                strokeWidth={2}
                x1={pad}
                x2={width - pad}
                y1={height / 2}
                y2={height / 2}
              />
              {dated.map((event, index) => {
                const x =
                  pad +
                  ((event.ts - minTs) / span) * (width - pad * 2);
                if (x < pad - 4 || x > width - pad + 4) return null;
                const y =
                  height / 2 + (index % 2 === 0 ? -28 : 28);
                return (
                  <g
                    key={event.event_id}
                    onMouseEnter={() => setHoverId(event.event_id)}
                    onMouseLeave={() => setHoverId(null)}
                  >
                    <line
                      stroke={TYPE_COLOR[event.bucket]}
                      strokeWidth={1.5}
                      x1={x}
                      x2={x}
                      y1={height / 2}
                      y2={y}
                    />
                    <circle
                      cx={x}
                      cy={y}
                      fill={TYPE_COLOR[event.bucket]}
                      r={hoverId === event.event_id ? 7 : 5}
                    >
                      <title>
                        {event.event_type}: {event.description}
                      </title>
                    </circle>
                  </g>
                );
              })}
            </svg>
            {hovered && (
              <div
                className="pointer-events-none absolute left-3 top-3 max-w-xs rounded-lg border border-border bg-surface px-3 py-2 text-caption shadow-md"
                role="tooltip"
              >
                <p className="font-medium text-foreground">
                  {hovered.event_type.replaceAll("_", " ")}
                </p>
                <p className="text-muted">{hovered.description}</p>
              </div>
            )}
            <ul className="mt-2 flex flex-wrap gap-2" aria-label="Timeline legend">
              {groups.map(([bucket, count]) => (
                <li
                  className="inline-flex items-center gap-1.5 text-micro text-muted"
                  key={bucket}
                >
                  <span
                    aria-hidden="true"
                    className="h-2.5 w-2.5 rounded-full"
                    style={{ background: TYPE_COLOR[bucket] }}
                  />
                  {bucket} ({count})
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
