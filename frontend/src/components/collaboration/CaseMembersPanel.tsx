import { Badge } from "../ui/Badge";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";
import { useCaseMembersQuery } from "../../hooks/useCollaboration";

export function CaseMembersPanel({ caseId }: { caseId: string }) {
  const query = useCaseMembersQuery(caseId);
  const items = query.data?.data.items ?? [];

  return (
    <Panel
      description="Investigators collaborating on this case."
      title="Team members"
    >
      {query.isLoading && <LoadingState label="Loading members" />}
      {query.isError && (
        <ErrorState description="Members could not be loaded." title="Error" />
      )}
      {query.isSuccess && items.length === 0 && (
        <p className="text-xs text-slate-500">No members yet.</p>
      )}
      <ul className="space-y-2">
        {items.map((member) => (
          <li
            className="flex items-center justify-between rounded-lg border border-slate-800 px-3 py-2 text-xs"
            key={member.id}
          >
            <span className="text-slate-200">
              {member.display_name || member.username || member.user_id}
            </span>
            <Badge tone="cyan">{member.role.replaceAll("_", " ")}</Badge>
          </li>
        ))}
      </ul>
    </Panel>
  );
}
