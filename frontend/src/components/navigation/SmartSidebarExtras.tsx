import { useMemo, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import {
  ChevronDown,
  Pin,
  Star,
  Clock3,
  Plus,
  Search,
  Command,
} from "lucide-react";

import { useOptionalProductivity } from "../../context/ProductivityContext";
import { useCasesQuery } from "../../hooks/useCases";
import { cn } from "../../lib/utils";
import { Input } from "../ui/Input";

function CollapsibleGroup({
  title,
  collapsedRail,
  children,
  defaultOpen = true,
}: {
  title: string;
  collapsedRail: boolean;
  children: ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  if (collapsedRail) {
    return null;
  }
  return (
    <div>
      <button
        className="mb-2 flex w-full items-center justify-between px-3 text-micro font-semibold uppercase tracking-[0.18em] text-subtle hover:text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        onClick={() => setOpen((current) => !current)}
        type="button"
      >
        {title}
        <ChevronDown
          aria-hidden="true"
          className={cn("duration-fast transition-transform", !open && "-rotate-90")}
          size={12}
        />
      </button>
      {open ? children : null}
    </div>
  );
}

export function SmartSidebarExtras({
  collapsed,
  onNavigate,
}: {
  collapsed: boolean;
  onNavigate: () => void;
}) {
  const productivity = useOptionalProductivity();
  const casesQuery = useCasesQuery();
  const [query, setQuery] = useState("");

  const cases = casesQuery.data?.data.items ?? [];
  const byId = useMemo(
    () => new Map(cases.map((item) => [item.id, item])),
    [cases],
  );

  if (!productivity) {
    return null;
  }

  const {
    recentCases,
    pinnedCaseIds,
    favoriteCaseIds,
    openInvestigation,
    openCommandPalette,
    togglePinned,
    toggleFavorite,
  } = productivity;

  const filtered = cases.filter((item) => {
    const needle = query.trim().toLowerCase();
    if (!needle) {
      return false;
    }
    return (
      item.title.toLowerCase().includes(needle) ||
      item.case_number.toLowerCase().includes(needle)
    );
  });

  return (
    <div className="space-y-5">
      {!collapsed && (
        <div className="px-1">
          <label className="relative block">
            <span className="sr-only">Search investigations</span>
            <Search
              aria-hidden="true"
              className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-subtle"
              size={14}
            />
            <Input
              className="h-9 pl-8 text-caption"
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search cases…"
              value={query}
            />
          </label>
          {filtered.length > 0 && (
            <ul className="mt-2 max-h-36 space-y-1 overflow-y-auto">
              {filtered.slice(0, 8).map((item) => (
                <li key={item.id}>
                  <button
                    className="w-full truncate rounded-md px-2 py-1.5 text-left text-caption text-muted hover:bg-surface-muted hover:text-foreground"
                    onClick={() => {
                      openInvestigation({
                        caseId: item.id,
                        title: item.title,
                        caseNumber: item.case_number,
                      });
                      onNavigate();
                    }}
                    type="button"
                  >
                    {item.case_number} · {item.title}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      <CollapsibleGroup collapsedRail={collapsed} title="Quick actions">
        <div className="space-y-1 px-1">
          <Link
            className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-muted hover:bg-surface-muted hover:text-foreground"
            onClick={onNavigate}
            to="/investigations"
          >
            <Plus size={15} /> New investigation
          </Link>
          <button
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-muted hover:bg-surface-muted hover:text-foreground"
            onClick={() => {
              openCommandPalette("commands");
              onNavigate();
            }}
            type="button"
          >
            <Command size={15} /> Command palette
          </button>
        </div>
      </CollapsibleGroup>

      <CollapsibleGroup collapsedRail={collapsed} title="Pinned">
        <ul className="space-y-1 px-1">
          {pinnedCaseIds.length === 0 && (
            <li className="px-3 text-caption text-subtle">No pinned cases</li>
          )}
          {pinnedCaseIds.map((id) => {
            const item = byId.get(id);
            if (!item) {
              return null;
            }
            return (
              <li className="flex items-center gap-1" key={id}>
                <button
                  className="min-w-0 flex-1 truncate rounded-lg px-3 py-2 text-left text-sm text-muted hover:bg-surface-muted hover:text-foreground"
                  onClick={() => {
                    openInvestigation({
                      caseId: item.id,
                      title: item.title,
                      caseNumber: item.case_number,
                    });
                    onNavigate();
                  }}
                  type="button"
                >
                  <Pin className="mr-2 inline text-primary" size={12} />
                  {item.case_number}
                </button>
                <button
                  aria-label="Unpin"
                  className="rounded p-1 text-subtle hover:text-foreground"
                  onClick={() => togglePinned(id)}
                  type="button"
                >
                  <Pin size={12} />
                </button>
              </li>
            );
          })}
        </ul>
      </CollapsibleGroup>

      <CollapsibleGroup collapsedRail={collapsed} title="Favorites">
        <ul className="space-y-1 px-1">
          {favoriteCaseIds.length === 0 && (
            <li className="px-3 text-caption text-subtle">No favorites</li>
          )}
          {favoriteCaseIds.map((id) => {
            const item = byId.get(id);
            if (!item) {
              return null;
            }
            return (
              <li key={id}>
                <button
                  className="flex w-full items-center gap-2 truncate rounded-lg px-3 py-2 text-left text-sm text-muted hover:bg-surface-muted hover:text-foreground"
                  onClick={() => {
                    openInvestigation({
                      caseId: item.id,
                      title: item.title,
                      caseNumber: item.case_number,
                    });
                    onNavigate();
                  }}
                  type="button"
                >
                  <Star className="text-warning" size={12} />
                  {item.case_number}
                </button>
              </li>
            );
          })}
        </ul>
      </CollapsibleGroup>

      <CollapsibleGroup collapsedRail={collapsed} defaultOpen title="Recent">
        <ul className="space-y-1 px-1">
          {recentCases.length === 0 && (
            <li className="px-3 text-caption text-subtle">No recent cases</li>
          )}
          {recentCases.slice(0, 6).map((item) => (
            <li key={item.id}>
              <button
                className="flex w-full items-center gap-2 truncate rounded-lg px-3 py-2 text-left text-sm text-muted hover:bg-surface-muted hover:text-foreground"
                onClick={() => {
                  openInvestigation({
                    caseId: item.id,
                    title: item.title,
                    caseNumber: item.caseNumber,
                  });
                  onNavigate();
                }}
                type="button"
              >
                <Clock3 size={12} />
                {item.caseNumber}
              </button>
              <div className="flex gap-1 px-3 pb-1">
                <button
                  aria-label="Pin case"
                  className="text-micro text-subtle hover:text-primary"
                  onClick={() => togglePinned(item.id)}
                  type="button"
                >
                  Pin
                </button>
                <button
                  aria-label="Favorite case"
                  className="text-micro text-subtle hover:text-warning"
                  onClick={() => toggleFavorite(item.id)}
                  type="button"
                >
                  Favorite
                </button>
              </div>
            </li>
          ))}
        </ul>
      </CollapsibleGroup>
    </div>
  );
}
