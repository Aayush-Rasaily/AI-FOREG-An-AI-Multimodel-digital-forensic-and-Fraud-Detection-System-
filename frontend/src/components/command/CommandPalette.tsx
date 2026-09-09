import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Clock3,
  FileArchive,
  FileBarChart,
  LayoutDashboard,
  Search,
  Settings,
  Shield,
  Sparkles,
} from "lucide-react";

import { useProductivity } from "../../context/ProductivityContext";
import { useCasesQuery } from "../../hooks/useCases";
import { cn } from "../../lib/utils";
import { Dialog } from "../ui/Dialog";
import { Input } from "../ui/Input";

interface CommandItem {
  id: string;
  label: string;
  hint?: string;
  group: string;
  keywords: string;
  action: () => void;
}

function highlight(text: string, query: string) {
  if (!query.trim()) {
    return text;
  }
  const index = text.toLowerCase().indexOf(query.toLowerCase());
  if (index < 0) {
    return text;
  }
  return (
    <>
      {text.slice(0, index)}
      <mark className="rounded-sm bg-primary-soft px-0.5 text-primary">
        {text.slice(index, index + query.length)}
      </mark>
      {text.slice(index + query.length)}
    </>
  );
}

export function CommandPalette() {
  const {
    commandOpen,
    commandMode,
    closeCommandPalette,
    openCommandPalette,
    recentCases,
    pinnedCaseIds,
    openInvestigation,
    navigateShortcut,
  } = useProductivity();
  const casesQuery = useCasesQuery();
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    if (commandOpen) {
      setQuery("");
      setActiveIndex(0);
    }
  }, [commandOpen]);

  const cases = casesQuery.data?.data.items ?? [];

  const items = useMemo(() => {
    const nav: CommandItem[] = [
      {
        id: "dashboard",
        label: "Dashboard",
        group: "Navigate",
        keywords: "home overview",
        action: () => navigateShortcut("/dashboard"),
      },
      {
        id: "investigations",
        label: "Investigations",
        group: "Navigate",
        keywords: "cases list",
        action: () => navigateShortcut("/investigations"),
      },
      {
        id: "evidence",
        label: "Evidence registry",
        group: "Navigate",
        keywords: "files artifacts",
        action: () => navigateShortcut("/evidence"),
      },
      {
        id: "reports",
        label: "Reports",
        group: "Navigate",
        keywords: "export forensic",
        action: () => navigateShortcut("/reports"),
      },
      {
        id: "settings",
        label: "Settings",
        group: "Navigate",
        keywords: "preferences theme",
        action: () => navigateShortcut("/settings"),
      },
      {
        id: "timeline-help",
        label: "Open investigation timeline",
        hint: "Use within an open case",
        group: "Workspace",
        keywords: "timeline chronology",
        action: () => {
          closeCommandPalette();
          navigate("/investigations");
        },
      },
      {
        id: "fusion-help",
        label: "Fusion / correlation views",
        hint: "Ctrl+Shift+F",
        group: "Workspace",
        keywords: "fusion correlation",
        action: () => {
          closeCommandPalette();
          navigate("/investigations");
        },
      },
      {
        id: "search-mode",
        label: "Global search",
        hint: "Cases · evidence · reports",
        group: "Search",
        keywords: "find query",
        action: () => openCommandPalette("search"),
      },
    ];

    const pinned: CommandItem[] = cases
      .filter((item) => pinnedCaseIds.includes(item.id))
      .map((item) => ({
        id: `pin-${item.id}`,
        label: `${item.case_number} · ${item.title}`,
        group: "Pinned",
        keywords: `${item.case_number} ${item.title} pinned`,
        action: () =>
          openInvestigation({
            caseId: item.id,
            title: item.title,
            caseNumber: item.case_number,
          }),
      }));

    const recent: CommandItem[] = recentCases.map((item) => ({
      id: `recent-${item.id}`,
      label: `${item.caseNumber} · ${item.title}`,
      group: "Recent",
      keywords: `${item.caseNumber} ${item.title} recent`,
      action: () =>
        openInvestigation({
          caseId: item.id,
          title: item.title,
          caseNumber: item.caseNumber,
        }),
    }));

    const caseHits: CommandItem[] = cases.map((item) => ({
      id: `case-${item.id}`,
      label: `${item.case_number} · ${item.title}`,
      hint: item.status,
      group: "Cases",
      keywords: `${item.case_number} ${item.title} ${item.status} case`,
      action: () =>
        openInvestigation({
          caseId: item.id,
          title: item.title,
          caseNumber: item.case_number,
        }),
    }));

    const help: CommandItem[] = [
      {
        id: "help-k",
        label: "Ctrl + K — Command palette",
        group: "Shortcuts",
        keywords: "keyboard help",
        action: () => undefined,
      },
      {
        id: "help-slash",
        label: "Ctrl + / — Shortcut help",
        group: "Shortcuts",
        keywords: "keyboard help",
        action: () => undefined,
      },
      {
        id: "help-f",
        label: "Ctrl + Shift + F — Fusion guidance",
        group: "Shortcuts",
        keywords: "keyboard fusion",
        action: () => undefined,
      },
      {
        id: "help-r",
        label: "Ctrl + Shift + R — Reports",
        group: "Shortcuts",
        keywords: "keyboard reports",
        action: () => undefined,
      },
      {
        id: "help-esc",
        label: "Esc — Close dialogs",
        group: "Shortcuts",
        keywords: "keyboard escape",
        action: () => undefined,
      },
    ];

    const pool =
      commandMode === "help"
        ? help
        : commandMode === "search"
          ? [...caseHits, ...pinned, ...recent, ...nav]
          : [...nav, ...pinned, ...recent, ...caseHits.slice(0, 8)];

    const needle = query.trim().toLowerCase();
    if (!needle) {
      return pool;
    }
    return pool.filter(
      (item) =>
        item.label.toLowerCase().includes(needle) ||
        item.keywords.toLowerCase().includes(needle) ||
        (item.hint?.toLowerCase().includes(needle) ?? false),
    );
  }, [
    cases,
    closeCommandPalette,
    commandMode,
    navigate,
    navigateShortcut,
    openCommandPalette,
    openInvestigation,
    pinnedCaseIds,
    query,
    recentCases,
  ]);

  useEffect(() => {
    setActiveIndex(0);
  }, [query, commandMode]);

  const runActive = () => {
    const item = items[activeIndex];
    if (!item) {
      return;
    }
    item.action();
    if (commandMode !== "help" && item.group !== "Shortcuts") {
      closeCommandPalette();
    }
  };

  const iconFor = (group: string) => {
    if (group === "Pinned") return <Shield size={14} />;
    if (group === "Recent") return <Clock3 size={14} />;
    if (group === "Cases") return <Search size={14} />;
    if (group === "Workspace") return <Sparkles size={14} />;
    if (group === "Search") return <FileArchive size={14} />;
    if (group === "Shortcuts") return <FileBarChart size={14} />;
    if (group === "Navigate") return <LayoutDashboard size={14} />;
    return <Settings size={14} />;
  };

  return (
    <Dialog
      className="max-w-xl"
      description="Jump to cases, evidence, reports, and workspace tools."
      onClose={closeCommandPalette}
      open={commandOpen}
      title={
        commandMode === "help"
          ? "Keyboard shortcuts"
          : commandMode === "search"
            ? "Global search"
            : "Command palette"
      }
    >
      <div className="space-y-3">
        <Input
          aria-label="Command search"
          autoFocus
          onChange={(event) => setQuery(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "ArrowDown") {
              event.preventDefault();
              setActiveIndex((current) =>
                Math.min(current + 1, Math.max(items.length - 1, 0)),
              );
            }
            if (event.key === "ArrowUp") {
              event.preventDefault();
              setActiveIndex((current) => Math.max(current - 1, 0));
            }
            if (event.key === "Enter") {
              event.preventDefault();
              runActive();
            }
          }}
          placeholder={
            commandMode === "help"
              ? "Filter shortcuts…"
              : "Search cases, evidence, reports, navigation…"
          }
          value={query}
        />
        <ul className="max-h-80 space-y-1 overflow-y-auto" role="listbox">
          {items.length === 0 && (
            <li className="px-2 py-6 text-center text-caption text-muted">
              No matches
            </li>
          )}
          {items.map((item, index) => (
            <li key={item.id}>
              <button
                aria-selected={index === activeIndex}
                className={cn(
                  "flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left duration-fast transition-colors",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                  index === activeIndex
                    ? "bg-primary-soft text-foreground"
                    : "hover:bg-surface-muted",
                )}
                onClick={() => {
                  setActiveIndex(index);
                  item.action();
                  if (commandMode !== "help" && item.group !== "Shortcuts") {
                    closeCommandPalette();
                  }
                }}
                onMouseEnter={() => setActiveIndex(index)}
                role="option"
                type="button"
              >
                <span className="text-muted">{iconFor(item.group)}</span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-body">
                    {highlight(item.label, query)}
                  </span>
                  <span className="block text-micro text-subtle">
                    {item.group}
                    {item.hint ? ` · ${item.hint}` : ""}
                  </span>
                </span>
              </button>
            </li>
          ))}
        </ul>
        <p className="text-micro text-subtle">
          ↑↓ to move · Enter to run · Esc to close · Ctrl+/ shortcuts
        </p>
      </div>
    </Dialog>
  );
}
