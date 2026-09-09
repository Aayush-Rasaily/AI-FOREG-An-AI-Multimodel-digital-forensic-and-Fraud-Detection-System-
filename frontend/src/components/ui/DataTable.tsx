import { useMemo, useState, type ReactNode } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

import { useViewport } from "../../hooks/useMediaQuery";
import { cn } from "../../lib/utils";
import { Button } from "./Button";
import { Checkbox } from "./Checkbox";
import { SearchInput } from "./SearchInput";

export type DataTableColumnPriority = "primary" | "secondary" | "tertiary";

export interface DataTableColumn<T> {
  key: string;
  header: string;
  sortable?: boolean;
  /** primary: always; secondary: tablet+; tertiary: desktop+ */
  priority?: DataTableColumnPriority;
  render?: (row: T) => ReactNode;
  value?: (row: T) => string | number;
}

interface DataTableProps<T> {
  columns: DataTableColumn<T>[];
  rows: T[];
  rowKey: (row: T) => string;
  pageSize?: number;
  compact?: boolean;
  selectable?: boolean;
  filterPlaceholder?: string;
}

function cellValue<T>(column: DataTableColumn<T>, row: T): ReactNode {
  if (column.render) {
    return column.render(row);
  }
  return String((row as Record<string, unknown>)[column.key] ?? "");
}

function priorityClass(priority: DataTableColumnPriority = "primary"): string {
  if (priority === "secondary") {
    return "hidden md:table-cell";
  }
  if (priority === "tertiary") {
    return "hidden desktop:table-cell";
  }
  return "";
}

export function DataTable<T>({
  columns,
  rows,
  rowKey,
  pageSize = 10,
  compact = false,
  selectable = false,
  filterPlaceholder = "Filter rows",
}: DataTableProps<T>) {
  const { isTabletUp } = useViewport();
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");
  const [page, setPage] = useState(0);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<string[]>([]);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    const next = needle
      ? rows.filter((row) =>
          columns.some((column) => {
            const raw = column.value
              ? String(column.value(row))
              : String((row as Record<string, unknown>)[column.key] ?? "");
            return raw.toLowerCase().includes(needle);
          }),
        )
      : [...rows];
    if (!sortKey) {
      return next;
    }
    const column = columns.find((item) => item.key === sortKey);
    return [...next].sort((left, right) => {
      const a = String(column?.value?.(left) ?? "");
      const b = String(column?.value?.(right) ?? "");
      return sortDir === "asc" ? a.localeCompare(b) : b.localeCompare(a);
    });
  }, [columns, query, rows, sortDir, sortKey]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / pageSize));
  const pageRows = filtered.slice(page * pageSize, page * pageSize + pageSize);
  const primaryColumns = columns.filter(
    (column) => (column.priority ?? "primary") === "primary",
  );
  const cardColumns =
    primaryColumns.length > 0 ? primaryColumns : columns.slice(0, 2);

  const toggleSort = (key: string) => {
    if (sortKey === key) {
      setSortDir((current) => (current === "asc" ? "desc" : "asc"));
      return;
    }
    setSortKey(key);
    setSortDir("asc");
  };

  return (
    <div className="space-y-3">
      <SearchInput
        onChange={(event) => {
          setQuery(event.target.value);
          setPage(0);
        }}
        placeholder={filterPlaceholder}
        value={query}
      />

      {!isTabletUp ? (
        <ul className="space-y-2">
          {pageRows.map((row) => {
            const id = rowKey(row);
            return (
              <li
                className="rounded-lg border border-border bg-surface p-3 shadow-sm duration-fast transition-colors hover:bg-surface-muted"
                key={id}
              >
                {selectable && (
                  <div className="mb-2">
                    <Checkbox
                      aria-label={`Select row ${id}`}
                      checked={selected.includes(id)}
                      onChange={() =>
                        setSelected((current) =>
                          current.includes(id)
                            ? current.filter((item) => item !== id)
                            : [...current, id],
                        )
                      }
                    />
                  </div>
                )}
                <dl className="space-y-2">
                  {cardColumns.map((column) => (
                    <div key={column.key}>
                      <dt className="text-micro uppercase tracking-wider text-subtle">
                        {column.header}
                      </dt>
                      <dd className="mt-0.5 break-words text-body text-foreground">
                        {cellValue(column, row)}
                      </dd>
                    </div>
                  ))}
                </dl>
              </li>
            );
          })}
        </ul>
      ) : (
        <div className="overflow-x-auto rounded-md border border-border">
          <table
            aria-label={filterPlaceholder}
            className={cn("ds-table w-full min-w-0 border-collapse text-left")}
            data-compact={compact ? "true" : undefined}
          >
            <thead className="sticky top-0 bg-surface-muted">
              <tr className="border-b border-border text-caption uppercase tracking-wider text-muted">
                {selectable && <th className="px-4 py-3">Select</th>}
                {columns.map((column) => (
                  <th
                    className={cn(
                      "px-4 py-3 font-medium",
                      priorityClass(column.priority),
                    )}
                    key={column.key}
                    scope="col"
                  >
                    {column.sortable ? (
                      <button
                        className="inline-flex items-center gap-1 text-left hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                        onClick={() => toggleSort(column.key)}
                        title={`Sort by ${column.header}`}
                        type="button"
                      >
                        {column.header}
                        {sortKey === column.key &&
                          (sortDir === "asc" ? (
                            <ChevronUp size={12} />
                          ) : (
                            <ChevronDown size={12} />
                          ))}
                      </button>
                    ) : (
                      column.header
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {pageRows.map((row) => {
                const id = rowKey(row);
                return (
                  <tr
                    className="border-b border-border hover:bg-surface-muted"
                    key={id}
                  >
                    {selectable && (
                      <td className="px-4 py-3">
                        <Checkbox
                          aria-label={`Select row ${id}`}
                          checked={selected.includes(id)}
                          onChange={() =>
                            setSelected((current) =>
                              current.includes(id)
                                ? current.filter((item) => item !== id)
                                : [...current, id],
                            )
                          }
                        />
                      </td>
                    )}
                    {columns.map((column) => (
                      <td
                        className={cn(
                          "px-4 py-3",
                          priorityClass(column.priority),
                        )}
                        key={column.key}
                      >
                        {cellValue(column, row)}
                      </td>
                    ))}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <div className="flex flex-wrap items-center justify-end gap-2">
        <Button
          disabled={page === 0}
          onClick={() => setPage((current) => Math.max(0, current - 1))}
          size="sm"
          type="button"
        >
          Previous
        </Button>
        <span className="text-caption text-muted">
          {page + 1} / {pageCount}
        </span>
        <Button
          disabled={page + 1 >= pageCount}
          onClick={() => setPage((current) => current + 1)}
          size="sm"
          type="button"
        >
          Next
        </Button>
      </div>
    </div>
  );
}
