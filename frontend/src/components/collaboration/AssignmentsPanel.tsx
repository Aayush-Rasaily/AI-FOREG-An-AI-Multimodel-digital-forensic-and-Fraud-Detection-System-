import { useQueries } from "@tanstack/react-query";

import { useCaseEvidenceQuery } from "../../hooks/useEvidence";
import { collaborationApi } from "../../services/api/collaboration";
import type { EvidenceAssignment } from "../../types/collaboration";
import { Badge } from "../ui/Badge";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

export function AssignmentsPanel({ caseId }: { caseId: string }) {
  const evidenceQuery = useCaseEvidenceQuery(caseId);
  const evidenceItems = evidenceQuery.data?.data.items ?? [];

  const assignmentQueries = useQueries({
    queries: evidenceItems.map((item) => ({
      queryKey: ["evidence", item.id, "assignments"] as const,
      queryFn: () => collaborationApi.listAssignments(item.id),
      enabled: Boolean(item.id),
    })),
  });

  const isLoading =
    evidenceQuery.isLoading ||
    assignmentQueries.some((query) => query.isLoading);
  const isError =
    evidenceQuery.isError || assignmentQueries.some((query) => query.isError);

  const rows: Array<EvidenceAssignment & { filename: string }> = [];
  for (let index = 0; index < evidenceItems.length; index += 1) {
    const evidence = evidenceItems[index];
    const payload = assignmentQueries[index]?.data?.data;
    for (const assignment of payload?.items ?? []) {
      rows.push({
        ...assignment,
        filename: evidence.original_filename ?? evidence.id.slice(0, 8),
      });
    }
  }

  return (
    <Panel
      description="Evidence work assigned to investigators."
      title="Assignments"
    >
      {isLoading && <LoadingState label="Loading assignments" />}
      {isError && (
        <ErrorState
          description="Assignments could not be loaded."
          title="Error"
        />
      )}
      {!isLoading && !isError && rows.length === 0 && (
        <EmptyState
          description="Assign evidence from the evidence workspace to track ownership here."
          title="No assignments"
        />
      )}
      <ul className="space-y-2">
        {rows.map((row) => (
          <li
            className="rounded-lg border border-slate-800 px-3 py-2 text-xs"
            key={row.id}
          >
            <p className="text-slate-200">{row.filename}</p>
            <div className="mt-1 flex flex-wrap gap-2">
              <Badge tone="cyan">{row.status}</Badge>
              <Badge tone="neutral">{row.priority}</Badge>
            </div>
            {row.notes ? (
              <p className="mt-1 text-slate-500">{row.notes}</p>
            ) : null}
          </li>
        ))}
      </ul>
    </Panel>
  );
}
