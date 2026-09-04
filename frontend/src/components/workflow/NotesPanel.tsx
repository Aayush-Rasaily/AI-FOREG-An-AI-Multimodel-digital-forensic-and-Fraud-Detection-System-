import { type FormEvent, useState } from "react";

import {
  useCreateWorkflowNoteMutation,
  useWorkflowNotesQuery,
} from "../../hooks/useWorkflow";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

export function NotesPanel({ caseId }: { caseId: string }) {
  const query = useWorkflowNotesQuery(caseId);
  const createNote = useCreateWorkflowNoteMutation(caseId);
  const [content, setContent] = useState("");
  const items = query.data?.data.items ?? [];

  async function onCreate(event: FormEvent) {
    event.preventDefault();
    if (!content.trim()) return;
    await createNote.mutateAsync(content.trim());
    setContent("");
  }

  return (
    <Panel
      description="Structured investigation notes with immutable edit history."
      title="Investigation Notes"
    >
      <div className="space-y-3 p-4">
        <form className="space-y-2" onSubmit={(event) => void onCreate(event)}>
          <textarea
            className="min-h-20 w-full rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-2 text-sm text-slate-200"
            onChange={(event) => setContent(event.target.value)}
            placeholder="Add an internal note (markdown supported)"
            value={content}
          />
          <Button disabled={createNote.isPending} size="sm" type="submit">
            Add note
          </Button>
        </form>
        {query.isLoading && <LoadingState label="Loading notes" />}
        {query.isError && (
          <ErrorState description="Notes could not be loaded." title="Error" />
        )}
        {!query.isLoading && !query.isError && items.length === 0 && (
          <EmptyState
            description="Capture analytical or procedural notes for this case."
            title="No notes"
          />
        )}
        <ul className="space-y-2">
          {items.map((note) => (
            <li
              className="rounded-lg border border-slate-800 px-3 py-2"
              key={note.id}
            >
              <div className="mb-1 flex gap-2 text-[11px] text-slate-500">
                <span>{note.category}</span>
                <span>{note.visibility}</span>
                <span>{note.created_at}</span>
              </div>
              <p className="whitespace-pre-wrap text-sm text-slate-200">
                {note.content_markdown}
              </p>
            </li>
          ))}
        </ul>
      </div>
    </Panel>
  );
}
