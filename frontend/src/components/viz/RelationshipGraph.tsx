import {
  Download,
  Expand,
  ImageDown,
  Maximize2,
  Minimize2,
  Search,
} from "lucide-react";
import { useMemo, useRef, useState } from "react";

import { exportSvgAsPng, exportSvgAsSvg } from "../../lib/chartExport";
import { cn } from "../../lib/utils";
import { Button } from "../ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";
import { Input } from "../ui/Input";
import type { GraphEdge, GraphNode } from "./types";

const KIND_COLOR: Record<GraphNode["kind"], string> = {
  case: "#2563eb",
  evidence: "#0891b2",
  timeline: "#7c3aed",
  fusion: "#d97706",
  correlation: "#16a34a",
  report: "#dc2626",
};

interface RelationshipGraphProps {
  title?: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  onInspect?: (node: GraphNode) => void;
}

function layoutNodes(nodes: GraphNode[], width: number, height: number) {
  const cx = width / 2;
  const cy = height / 2;
  const radius = Math.min(width, height) * 0.36;
  const byKind = new Map<string, GraphNode[]>();
  for (const node of nodes) {
    const list = byKind.get(node.kind) ?? [];
    list.push(node);
    byKind.set(node.kind, list);
  }
  const kinds = [...byKind.keys()];
  const positions = new Map<string, { x: number; y: number }>();
  let globalIndex = 0;
  for (const kind of kinds) {
    const group = byKind.get(kind) ?? [];
    group.forEach((node, i) => {
      const angle =
        ((globalIndex + i) / Math.max(nodes.length, 1)) * Math.PI * 2 -
        Math.PI / 2;
      const ring = radius * (0.55 + (kinds.indexOf(kind) % 3) * 0.18);
      positions.set(node.id, {
        x: cx + Math.cos(angle) * ring,
        y: cy + Math.sin(angle) * ring,
      });
    });
    globalIndex += group.length;
  }
  return positions;
}

export function RelationshipGraph({
  title = "Evidence relationship graph",
  nodes,
  edges,
  onInspect,
}: RelationshipGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [fullscreen, setFullscreen] = useState(false);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [dragging, setDragging] = useState<{
    x: number;
    y: number;
  } | null>(null);

  const width = 720;
  const height = 420;
  const positions = useMemo(
    () => layoutNodes(nodes, width, height),
    [nodes],
  );

  const connected = useMemo(() => {
    if (!selectedId) {
      return new Set<string>();
    }
    const set = new Set<string>([selectedId]);
    for (const edge of edges) {
      if (edge.source === selectedId) set.add(edge.target);
      if (edge.target === selectedId) set.add(edge.source);
    }
    return set;
  }, [edges, selectedId]);

  const needle = query.trim().toLowerCase();
  const matchIds = useMemo(() => {
    if (!needle) return null;
    return new Set(
      nodes
        .filter(
          (n) =>
            n.label.toLowerCase().includes(needle) ||
            n.kind.includes(needle) ||
            (n.detail ?? "").toLowerCase().includes(needle),
        )
        .map((n) => n.id),
    );
  }, [needle, nodes]);

  const selected = nodes.find((n) => n.id === selectedId);

  return (
    <Card
      className={cn(
        "min-w-0",
        fullscreen &&
          "fixed inset-3 z-50 overflow-auto bg-surface shadow-xl md:inset-6",
      )}
    >
      <CardHeader className="flex-col items-stretch gap-3">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <CardTitle>{title}</CardTitle>
            <p className="mt-1 text-caption text-muted">
              Zoom, pan, search, and inspect linked forensic entities
            </p>
          </div>
          <div className="flex flex-wrap gap-1">
            <Button
              aria-label="Zoom out graph"
              onClick={() => setZoom((z) => Math.max(0.4, z - 0.15))}
              size="sm"
              type="button"
              variant="ghost"
            >
              −
            </Button>
            <Button
              aria-label="Zoom in graph"
              onClick={() => setZoom((z) => Math.min(2.5, z + 0.15))}
              size="sm"
              type="button"
              variant="ghost"
            >
              +
            </Button>
            <Button
              aria-label="Reset graph view"
              onClick={() => {
                setZoom(1);
                setPan({ x: 0, y: 0 });
              }}
              size="sm"
              type="button"
              variant="ghost"
            >
              <Maximize2 aria-hidden="true" size={14} />
            </Button>
            <Button
              aria-label={fullscreen ? "Exit fullscreen" : "Fullscreen graph"}
              onClick={() => setFullscreen((v) => !v)}
              size="sm"
              type="button"
              variant="secondary"
            >
              {fullscreen ? (
                <Minimize2 aria-hidden="true" size={14} />
              ) : (
                <Expand aria-hidden="true" size={14} />
              )}
            </Button>
            <Button
              aria-label="Export graph SVG"
              onClick={() => {
                if (svgRef.current) exportSvgAsSvg(svgRef.current, "relationship-graph.svg");
              }}
              size="sm"
              type="button"
              variant="secondary"
            >
              <Download aria-hidden="true" size={14} />
              SVG
            </Button>
            <Button
              aria-label="Export graph PNG"
              onClick={() => {
                if (svgRef.current) void exportSvgAsPng(svgRef.current, "relationship-graph.png");
              }}
              size="sm"
              type="button"
              variant="secondary"
            >
              <ImageDown aria-hidden="true" size={14} />
              PNG
            </Button>
          </div>
        </div>
        <label className="relative max-w-md">
          <span className="sr-only">Search graph nodes</span>
          <Search
            aria-hidden="true"
            className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-subtle"
            size={14}
          />
          <Input
            className="pl-8"
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search nodes…"
            value={query}
          />
        </label>
      </CardHeader>
      <CardContent className="space-y-3">
        {nodes.length === 0 ? (
          <p className="py-12 text-center text-caption text-muted">
            No relationship signals yet. Cases and analytics populate this graph.
          </p>
        ) : (
          <>
            <div
              className="overflow-hidden rounded-xl border border-border bg-background/40"
              onMouseLeave={() => setDragging(null)}
              onMouseMove={(event) => {
                if (!dragging) return;
                const dx = event.clientX - dragging.x;
                const dy = event.clientY - dragging.y;
                setPan((current) => ({
                  x: current.x + dx,
                  y: current.y + dy,
                }));
                setDragging({ x: event.clientX, y: event.clientY });
              }}
              onMouseUp={() => setDragging(null)}
            >
              <svg
                aria-label={title}
                className="h-[280px] w-full touch-none sm:h-[360px] md:h-[420px]"
                ref={svgRef}
                role="img"
                viewBox={`0 0 ${width} ${height}`}
                onMouseDown={(event) => {
                  if ((event.target as Element).tagName === "svg") {
                    setDragging({ x: event.clientX, y: event.clientY });
                  }
                }}
              >
                <g transform={`translate(${pan.x} ${pan.y}) scale(${zoom})`}>
                  {edges.map((edge) => {
                    const a = positions.get(edge.source);
                    const b = positions.get(edge.target);
                    if (!a || !b) return null;
                    const highlight =
                      !selectedId ||
                      connected.has(edge.source) ||
                      connected.has(edge.target);
                    return (
                      <line
                        key={edge.id}
                        opacity={highlight ? 0.7 : 0.15}
                        stroke="var(--color-border-strong, #94a3b8)"
                        strokeWidth={1.5}
                        x1={a.x}
                        x2={b.x}
                        y1={a.y}
                        y2={b.y}
                      />
                    );
                  })}
                  {nodes.map((node) => {
                    const pos = positions.get(node.id);
                    if (!pos) return null;
                    const dimmed =
                      (selectedId && !connected.has(node.id)) ||
                      (matchIds && !matchIds.has(node.id));
                    return (
                      <g
                        className="cursor-pointer"
                        key={node.id}
                        onClick={() => {
                          setSelectedId(node.id);
                          onInspect?.(node);
                        }}
                        transform={`translate(${pos.x} ${pos.y})`}
                      >
                        <circle
                          fill={KIND_COLOR[node.kind]}
                          opacity={dimmed ? 0.25 : 1}
                          r={selectedId === node.id ? 16 : 12}
                          stroke="var(--color-surface, #fff)"
                          strokeWidth={2}
                        />
                        <text
                          dy={28}
                          fill="var(--color-foreground, #0f172a)"
                          fontSize="10"
                          opacity={dimmed ? 0.3 : 1}
                          textAnchor="middle"
                        >
                          {node.label.length > 18
                            ? `${node.label.slice(0, 17)}…`
                            : node.label}
                        </text>
                      </g>
                    );
                  })}
                </g>
              </svg>
            </div>
            <ul className="flex flex-wrap gap-2" aria-label="Graph legend">
              {(Object.keys(KIND_COLOR) as Array<GraphNode["kind"]>).map(
                (kind) => (
                  <li
                    className="inline-flex items-center gap-1.5 text-micro text-muted"
                    key={kind}
                  >
                    <span
                      aria-hidden="true"
                      className="h-2.5 w-2.5 rounded-full"
                      style={{ background: KIND_COLOR[kind] }}
                    />
                    {kind}
                  </li>
                ),
              )}
            </ul>
            {selected && (
              <div
                aria-live="polite"
                className="rounded-lg border border-border bg-surface-muted/40 p-3"
              >
                <p className="text-caption font-medium text-foreground">
                  Inspect · {selected.label}
                </p>
                <p className="mt-1 text-caption text-muted">
                  {selected.kind}
                  {selected.detail ? ` · ${selected.detail}` : ""}
                </p>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
