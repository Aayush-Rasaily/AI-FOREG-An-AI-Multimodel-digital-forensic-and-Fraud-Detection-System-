import { type FormEvent, useState } from "react";

import {
  useCaseCommentsQuery,
  useCreateCommentMutation,
} from "../../hooks/useCollaboration";
import { Button } from "../ui/Button";
import { ErrorState } from "../ui/ErrorState";
import { Input } from "../ui/Input";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

export function CommentsPanel({ caseId }: { caseId: string }) {
  const query = useCaseCommentsQuery(caseId);
  const createComment = useCreateCommentMutation(caseId);
  const [body, setBody] = useState("");
  const items = query.data?.data.items ?? [];

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!body.trim()) return;
    await createComment.mutateAsync(body.trim());
    setBody("");
  }

  return (
    <Panel
      description="Threaded discussion that never alters forensic data."
      title="Comments"
    >
      <form className="mb-3 flex gap-2" onSubmit={onSubmit}>
        <Input
          onChange={(event) => setBody(event.target.value)}
          placeholder="Add a comment… use @username to mention"
          value={body}
        />
        <Button disabled={createComment.isPending} size="sm" type="submit">
          Post
        </Button>
      </form>
      {query.isLoading && <LoadingState label="Loading comments" />}
      {query.isError && (
        <ErrorState description="Comments could not be loaded." title="Error" />
      )}
      <ul className="space-y-2">
        {items.map((comment) => (
          <li
            className="rounded-lg border border-slate-800 px-3 py-2 text-xs"
            key={comment.id}
          >
            <p className="text-slate-500">
              {comment.author_username || "user"} ·{" "}
              {new Date(comment.created_at).toLocaleString()}
              {comment.parent_id ? " · reply" : ""}
            </p>
            <p className="mt-1 text-slate-200">{comment.body}</p>
          </li>
        ))}
      </ul>
    </Panel>
  );
}
