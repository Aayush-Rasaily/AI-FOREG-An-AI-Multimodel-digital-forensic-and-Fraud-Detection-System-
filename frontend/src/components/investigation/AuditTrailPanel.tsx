import {
  ChevronDown,
  ChevronRight,
  Download,
  Search,
  Shield,
  ShieldCheck,
} from "lucide-react";
import { useMemo, useState } from "react";

import {
  useAuditEventsQuery,
  useIntegrityVerifyMutation,
} from "../../hooks/useAudit";
import { ApiClientError } from "../../services/api/client";
import { auditService } from "../../services/api/audit";
import type { AuditEvent } from "../../types/audit";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

interface AuditTrailPanelProps {
  caseId: string;
}

const CATEGORY_TONE: Record<
  string,
  "neutral" | "primary" | "success" | "warning" | "error"
> = {
  case: "primary",
  evidence: "success",
  analysis: "warning",
  report: "neutral",
  user: "neutral",
  system: "neutral",
};

function formatTimestamp(ts: string): string {
  try {
    return new Date(ts).toLocaleString();
  } catch {
    return ts;
  }
}

export function AuditTrailPanel({ caseId }: AuditTrailPanelProps) {
  const eventsQuery = useAuditEventsQuery(caseId);
  const verifyMutation = useIntegrityVerifyMutation();
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [filter, setFilter] = useState("");

  const isNotFound =
    eventsQuery.error instanceof ApiClientError &&
    eventsQuery.error.status === 404;

  const events: AuditEvent[] = eventsQuery.data?.data.items ?? [];
  const total = eventsQuery.data?.data.total ?? 0;

  const filtered = useMemo(() => {
    if (!filter) return events;
    const q = filter.toLowerCase();
    return events.filter(
      (e) =>
        e.operation.toLowerCase().includes(q) ||
        e.category.toLowerCase().includes(q) ||
        e.user.toLowerCase().includes(q) ||
        (e.integrity_hash ?? "").toLowerCase().includes(q),
    );
  }, [events, filter]);

  const integrityResults = verifyMutation.data?.data;

  return (
    <Panel
      description="Immutable audit trail recording every investigator action and system operation."
      title="Audit Trail"
    >
      <div className="space-y-4 p-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Badge tone="neutral">{total} events</Badge>
            {integrityResults && (
              <Badge
                tone={
                  integrityResults.overall_status === "VERIFIED"
                    ? "success"
                    : integrityResults.overall_status === "MISMATCH"
                      ? "error"
                      : "warning"
                }
              >
                {integrityResults.overall_status}
              </Badge>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              disabled={verifyMutation.isPending}
              onClick={() =>
                verifyMutation.mutate({ case_id: caseId })
              }
              size="sm"
              variant="secondary"
            >
              <ShieldCheck size={14} />{" "}
              {verifyMutation.isPending
                ? "Verifying…"
                : "Verify Integrity"}
            </Button>
            <Button
              onClick={() =>
                window.open(
                  auditService.exportUrl(caseId),
                  "_blank",
                )
              }
              size="sm"
              variant="secondary"
            >
              <Download size={14} /> Export
            </Button>
          </div>
        </div>

        <div className="relative">
          <Search
            className="absolute left-3 top-1/2 -translate-y-1/2 text-muted"
            size={14}
          />
          <input
            className="w-full rounded-lg border border-border bg-background/40 py-2 pl-9 pr-3 text-xs text-foreground placeholder:text-subtle focus:border-primary-strong focus:outline-none"
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Filter events…"
            type="text"
            value={filter}
          />
        </div>

        {eventsQuery.isLoading && (
          <LoadingState label="Loading audit events…" />
        )}

        {!eventsQuery.isLoading &&
          eventsQuery.isError &&
          !isNotFound && (
            <ErrorState
              description="Unable to load audit events."
              title="Audit trail unavailable"
            />
          )}

        {!eventsQuery.isLoading &&
          (isNotFound || events.length === 0) &&
          !eventsQuery.isError && (
            <EmptyState
              description="No audit events recorded for this case."
              icon={<Shield aria-hidden="true" size={19} />}
              title="No audit events"
            />
          )}

        {filtered.length > 0 && (
          <div className="space-y-2">
            {filtered.map((event) => {
              const isOpen = expanded[event.id] ?? false;
              return (
                <div
                  className="rounded-lg border border-border bg-background/40 p-3"
                  key={event.id}
                >
                  <button
                    className="flex w-full items-center gap-2 text-left text-xs text-foreground"
                    onClick={() =>
                      setExpanded((c) => ({
                        ...c,
                        [event.id]: !isOpen,
                      }))
                    }
                    type="button"
                  >
                    {isOpen ? (
                      <ChevronDown size={14} />
                    ) : (
                      <ChevronRight size={14} />
                    )}
                    <Badge
                      tone={CATEGORY_TONE[event.category] ?? "neutral"}
                    >
                      {event.category}
                    </Badge>
                    <span className="font-medium">
                      {event.operation}
                    </span>
                    <span className="ml-auto text-muted">
                      {formatTimestamp(event.timestamp)}
                    </span>
                  </button>
                  {isOpen && (
                    <div className="mt-2 space-y-1 text-[11px] text-muted">
                      <p>User: {event.user}</p>
                      <p>
                        Integrity:{" "}
                        {event.integrity_hash.slice(0, 16)}…
                      </p>
                      {event.sha256_checksum && (
                        <p>
                          SHA-256:{" "}
                          {event.sha256_checksum.slice(0, 16)}…
                        </p>
                      )}
                      {event.client_ip && (
                        <p>IP: {event.client_ip}</p>
                      )}
                      <p>
                        Engine: {event.engine_version} · Policy:{" "}
                        {event.policy_version}
                      </p>
                      {(event.previous_state != null ||
                        event.new_state != null) && (
                        <pre className="mt-1 overflow-x-auto rounded bg-background-offset p-2">
                          {JSON.stringify(
                            {
                              previous_state: event.previous_state,
                              new_state: event.new_state,
                            },
                            null,
                            2,
                          )}
                        </pre>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {integrityResults &&
          integrityResults.results.length > 0 && (
            <div className="rounded-lg border border-border p-3">
              <p className="mb-2 text-xs font-medium text-foreground">
                Integrity Verification
              </p>
              <ul className="space-y-1 text-xs text-muted">
                {integrityResults.results.map((r, i) => (
                  <li key={i}>
                    <Badge
                      tone={
                        r.status === "VERIFIED"
                          ? "success"
                          : r.status === "MISMATCH"
                            ? "error"
                            : "warning"
                      }
                    >
                      {r.status}
                    </Badge>{" "}
                    {r.target_type} {r.target_id.slice(0, 8)}… —{" "}
                    {r.detail}
                  </li>
                ))}
              </ul>
            </div>
          )}
      </div>
    </Panel>
  );
}
