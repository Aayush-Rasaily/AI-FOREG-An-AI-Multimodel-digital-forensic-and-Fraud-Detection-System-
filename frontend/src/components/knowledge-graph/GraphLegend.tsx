import { Panel } from "../ui/Panel";

const LEGEND: { type: string; color: string }[] = [
  { type: "CASE", color: "#22d3ee" },
  { type: "EVIDENCE", color: "#38bdf8" },
  { type: "EMAIL / PHONE", color: "#a3e635" },
  { type: "HASH / FILE", color: "#fbbf24" },
  { type: "AI_FINDING", color: "#f472b6" },
  { type: "TIMELINE_EVENT", color: "#c084fc" },
  { type: "Other", color: "#94a3b8" },
];

export function GraphLegend() {
  return (
    <Panel description="Node category colors for the knowledge graph." title="Legend">
      <ul className="grid gap-2 p-4 sm:grid-cols-2">
        {LEGEND.map((item) => (
          <li className="flex items-center gap-2 text-xs text-slate-400" key={item.type}>
            <span
              aria-hidden="true"
              className="inline-block h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: item.color }}
            />
            {item.type}
          </li>
        ))}
      </ul>
    </Panel>
  );
}

export function nodeColor(entityType: string): string {
  if (entityType === "CASE") return "#22d3ee";
  if (entityType === "EVIDENCE") return "#38bdf8";
  if (entityType === "EMAIL" || entityType === "PHONE") return "#a3e635";
  if (entityType === "HASH" || entityType === "FILE" || entityType === "IMAGE") {
    return "#fbbf24";
  }
  if (entityType === "AI_FINDING") return "#f472b6";
  if (entityType === "TIMELINE_EVENT") return "#c084fc";
  return "#94a3b8";
}
