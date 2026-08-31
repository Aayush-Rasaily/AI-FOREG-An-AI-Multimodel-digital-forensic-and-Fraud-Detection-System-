import { useMemo, useState } from "react";
import type { FormEvent } from "react";
import { Filter, FolderPlus, ListFilter, Search } from "lucide-react";
import { Link } from "react-router-dom";

import { useCasesQuery, useCreateCaseMutation } from "../hooks/useCases";
import { PageHeader } from "../components/layout/PageHeader";
import { ApiClientError } from "../services/api/client";
import { Button } from "../components/ui/Button";
import { Dialog } from "../components/ui/Dialog";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorState } from "../components/ui/ErrorState";
import { Input } from "../components/ui/Input";
import { Select } from "../components/ui/Select";
import { Card } from "../components/ui/Card";
import { LoadingState } from "../components/ui/LoadingState";
import { Badge } from "../components/ui/Badge";
import type { CasePriority } from "../types/case";

export function InvestigationsPage() {
  const [createOpen, setCreateOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState<CasePriority>("MEDIUM");
  const casesQuery = useCasesQuery();
  const createCase = useCreateCaseMutation();
  const cases = casesQuery.data?.data.items ?? [];
  const filteredCases = useMemo(
    () =>
      cases.filter((item) => {
        const needle = search.trim().toLowerCase();
        return (
          !needle ||
          item.case_number.toLowerCase().includes(needle) ||
          item.title.toLowerCase().includes(needle)
        );
      }),
    [cases, search],
  );

  const submitCase = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await createCase.mutateAsync({ title: title.trim(), description: description.trim() || undefined, priority });
    setTitle("");
    setDescription("");
    setPriority("MEDIUM");
    setCreateOpen(false);
  };

  return (
    <div>
      <PageHeader
        actions={
          <Button onClick={() => setCreateOpen(true)} variant="primary">
            <FolderPlus aria-hidden="true" size={16} />
            Create investigation
          </Button>
        }
        description="Review, triage, and enter controlled investigation workspaces."
        eyebrow="Case management"
        title="Investigations"
      />

      <Card className="mb-4 p-3">
        <div className="flex flex-col gap-3 lg:flex-row">
          <label className="relative min-w-0 flex-1">
            <span className="sr-only">Search investigations</span>
            <Search
              aria-hidden="true"
              className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-600"
              size={16}
            />
            <Input
              className="pl-9"
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search by case ID or name"
              value={search}
            />
          </label>
          <div className="grid grid-cols-2 gap-3 sm:flex">
            <label>
              <span className="sr-only">Filter by status</span>
              <Select aria-label="Filter by status" defaultValue="all">
                <option value="all">All statuses</option>
                <option value="active">Active</option>
                <option value="closed">Closed</option>
              </Select>
            </label>
            <label>
              <span className="sr-only">Sort investigations</span>
              <Select aria-label="Sort investigations" defaultValue="recent">
                <option value="recent">Most recent</option>
                <option value="priority">Priority</option>
                <option value="oldest">Oldest</option>
              </Select>
            </label>
            <Button aria-label="Open advanced filters" size="md" variant="ghost">
              <Filter aria-hidden="true" size={16} />
              <span className="hidden sm:inline">Filters</span>
            </Button>
          </div>
        </div>
        {search && (
          <p className="mt-3 flex items-center gap-2 text-[11px] text-slate-600">
            <ListFilter aria-hidden="true" size={13} />
            Search is ready for connected case data: “{search}”
          </p>
        )}
      </Card>

      <Card>
        {casesQuery.isPending && <LoadingState label="Loading cases" />}
        {casesQuery.isError && (
          <ErrorState
            description={
              casesQuery.error instanceof ApiClientError
                ? casesQuery.error.message
                : "Cases could not be loaded from the backend."
            }
            onRetry={() => void casesQuery.refetch()}
          />
        )}
        {casesQuery.isSuccess && filteredCases.length === 0 && (
          <EmptyState
            description={
              search
                ? "No connected cases match the current search."
                : "Create the first case to begin preserving evidence and custody history."
            }
            icon={<FolderPlus aria-hidden="true" size={20} />}
            title={search ? "No matching cases" : "No investigations found"}
            action={
              !search && (
                <Button onClick={() => setCreateOpen(true)} variant="secondary">
                  <FolderPlus aria-hidden="true" size={16} />
                  Create case
                </Button>
              )
            }
          />
        )}
        {casesQuery.isSuccess && filteredCases.length > 0 && (
          <div className="divide-y divide-slate-800">
            {filteredCases.map((item) => (
              <Link
                className="grid gap-3 p-4 transition-colors hover:bg-slate-900/70 md:grid-cols-[1.2fr_1fr_0.8fr_0.8fr]"
                key={item.id}
                to={`/investigations/${item.id}`}
              >
                <div className="min-w-0">
                  <p className="text-[11px] font-medium text-cyan-300">{item.case_number}</p>
                  <p className="mt-1 truncate text-sm font-medium text-slate-100">{item.title}</p>
                </div>
                <div>
                  <p className="text-[10px] uppercase tracking-wider text-slate-600">Status</p>
                  <Badge className="mt-1" tone={item.status === "COMPLETED" ? "green" : "cyan"}>
                    {item.status.replaceAll("_", " ")}
                  </Badge>
                </div>
                <div>
                  <p className="text-[10px] uppercase tracking-wider text-slate-600">Priority</p>
                  <p className="mt-1 text-xs text-slate-300">{item.priority}</p>
                </div>
                <div>
                  <p className="text-[10px] uppercase tracking-wider text-slate-600">Created</p>
                  <p className="mt-1 text-xs text-slate-400">
                    {new Date(item.created_at).toLocaleDateString()}
                  </p>
                </div>
              </Link>
            ))}
          </div>
        )}
      </Card>

      <Dialog
        description="Create a persistent case container before registering original evidence."
        onClose={() => setCreateOpen(false)}
        open={createOpen}
        title="Create case"
      >
        <form className="space-y-4" onSubmit={submitCase}>
          <label className="block text-xs text-slate-400">
            Case title
            <Input className="mt-2" onChange={(event) => setTitle(event.target.value)} required value={title} />
          </label>
          <label className="block text-xs text-slate-400">
            Description
            <textarea
              className="mt-2 min-h-24 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200 outline-none focus:border-cyan-400"
              onChange={(event) => setDescription(event.target.value)}
              value={description}
            />
          </label>
          <label className="block text-xs text-slate-400">
            Priority
            <Select className="mt-2 w-full" onChange={(event) => setPriority(event.target.value as CasePriority)} value={priority}>
              <option value="LOW">Low</option>
              <option value="MEDIUM">Medium</option>
              <option value="HIGH">High</option>
              <option value="CRITICAL">Critical</option>
            </Select>
          </label>
          {createCase.isError && (
            <p className="text-xs text-red-300">
              {createCase.error instanceof ApiClientError
                ? createCase.error.message
                : "The case could not be created."}
            </p>
          )}
          <div className="flex justify-end gap-2">
            <Button onClick={() => setCreateOpen(false)} type="button" variant="ghost">Cancel</Button>
            <Button disabled={!title.trim() || createCase.isPending} type="submit" variant="primary">
              {createCase.isPending ? "Creating..." : "Create case"}
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}

