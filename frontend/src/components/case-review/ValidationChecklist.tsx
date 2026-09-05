import type { ChecklistItem } from "../../types/caseReview";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { Panel } from "../ui/Panel";

interface ValidationChecklistProps {
  items: ChecklistItem[];
  search: string;
  statusFilter: string;
  onMarkPass?: (itemId: string) => void;
}

export function ValidationChecklist({
  items,
  search,
  statusFilter,
  onMarkPass,
}: ValidationChecklistProps) {
  const needle = search.trim().toLowerCase();
  const filtered = items.filter((item) => {
    if (statusFilter !== "all" && item.status !== statusFilter) {
      return false;
    }
    if (!needle) {
      return true;
    }
    return (
      item.title.toLowerCase().includes(needle) ||
      item.item_code.toLowerCase().includes(needle) ||
      item.notes.toLowerCase().includes(needle)
    );
  });

  return (
    <Panel
      description="Deterministic validation checklist. Suggested status is advisory only."
      title="Validation Checklist"
    >
      <div className="space-y-3 p-4">
        {filtered.length === 0 ? (
          <p className="text-xs text-slate-500">No checklist items match.</p>
        ) : null}
        {filtered.map((item) => (
          <div
            className="border-b border-slate-800/80 pb-3 last:border-0"
            key={item.item_key}
          >
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm text-slate-200">{item.title}</span>
              <Badge tone={item.blocking ? "red" : "neutral"}>
                {item.status}
              </Badge>
              <Badge tone="cyan">suggest {item.suggested_status}</Badge>
              {item.outstanding ? (
                <Badge tone="amber">outstanding</Badge>
              ) : null}
            </div>
            <p className="mt-1 text-xs text-slate-500">{item.notes}</p>
            {item.provenance?.engine_version ? (
              <p className="mt-1 text-[11px] text-slate-600">
                Provenance · {String(item.provenance.engine_version)}
              </p>
            ) : null}
            {item.id && onMarkPass && item.status === "PENDING" ? (
              <Button
                className="mt-2"
                onClick={() => onMarkPass(item.id!)}
                size="sm"
                variant="secondary"
              >
                Mark PASS
              </Button>
            ) : null}
          </div>
        ))}
      </div>
    </Panel>
  );
}
