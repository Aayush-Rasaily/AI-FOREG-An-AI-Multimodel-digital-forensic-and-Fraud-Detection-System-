import { Link, useNavigate, useParams } from "react-router-dom";
import { X } from "lucide-react";

import { useProductivity } from "../../context/ProductivityContext";
import { cn } from "../../lib/utils";

export function InvestigationTabBar() {
  const { caseId } = useParams<{ caseId: string }>();
  const navigate = useNavigate();
  const { openTabs, closeInvestigationTab } = useProductivity();

  if (openTabs.length === 0) {
    return null;
  }

  return (
    <div
      aria-label="Open investigations"
      className="mb-3 flex gap-1 overflow-x-auto border-b border-border pb-2"
      role="tablist"
    >
      {openTabs.map((tab) => {
        const active = tab.caseId === caseId;
        return (
          <div
            className={cn(
              "flex min-w-0 shrink-0 items-center gap-1 rounded-lg border px-2 py-1.5 text-caption",
              active
                ? "border-primary/40 bg-primary-soft text-foreground"
                : "border-border bg-surface text-muted hover:bg-surface-muted",
            )}
            key={tab.caseId}
          >
            <Link
              className="max-w-[10rem] truncate focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring sm:max-w-[14rem]"
              title={`${tab.caseNumber} · ${tab.title}`}
              to={`/investigations/${tab.caseId}`}
            >
              {tab.dirty ? "• " : ""}
              {tab.caseNumber}
            </Link>
            <button
              aria-label={`Close ${tab.caseNumber}`}
              className="rounded-md p-1 text-subtle hover:bg-background hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              onClick={() => {
                closeInvestigationTab(tab.caseId);
                if (active) {
                  const remaining = openTabs.filter(
                    (item) => item.caseId !== tab.caseId,
                  );
                  navigate(
                    remaining[0]
                      ? `/investigations/${remaining[0].caseId}`
                      : "/investigations",
                  );
                }
              }}
              type="button"
            >
              <X size={12} />
            </button>
          </div>
        );
      })}
    </div>
  );
}
