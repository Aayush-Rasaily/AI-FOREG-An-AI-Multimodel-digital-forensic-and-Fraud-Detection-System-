import { useMemo, useState, type ReactNode } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

import { cn } from "../../lib/utils";
import { Button } from "./Button";
import { Checkbox } from "./Checkbox";
import { SearchInput } from "./SearchInput";

export interface DataTableColumn<T> {
  key: string;
  header: string;
  sortable?: boolean;
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

export function DataTable<T>({
  columns,
  rows,
  rowKey,
  pageSize = 10,
  compact = false,
  selectable = false,
  filterPlaceholder = "Filter rows",
}: DataTableProps<T>) {
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
      <div className="overflow-x-auto rounded-md border border-border">
        <table
          className={cn(
            "ds-table w-full border-collapse text-left text-body",
            compact && "text-caption",
          )}
        >
          <thead className="sticky top-0 bg-surface-muted">
            <tr className="border-b border-border text-caption uppercase tracking-wider text-muted">
              {selectable && <th className="px-4 py-3">Select</th>}
              {columns.map((column) => (
                <th className="px-4 py-3 font-medium" key={column.key} scope="col">
                  {column.sortable ? (
                    <button
                      className="inline-flex items-center gap-1"
                      onClick={() => toggleSort(column.key)}
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
                    <td className="px-4 py-3" key={column.key}>
                      {column.render
                        ? column.render(row)
                        : String(
                            (row as Record<string, unknown>)[column.key] ?? "",
                          )}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-end gap-2">
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
