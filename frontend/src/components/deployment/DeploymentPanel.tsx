import { useState } from "react";
import { ShieldCheck, FlaskConical } from "lucide-react";

import {
  useSystemReleaseCheckMutation,
  useSystemValidateMutation,
  useSystemVersionQuery,
} from "../../hooks/useSystemStatus";
import type { SystemReleaseCheck, SystemValidationResult } from "../../types/system";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

function toneFor(status: string): "green" | "amber" | "red" | "neutral" {
  const value = status.toUpperCase();
  if (value === "PASSED" || value === "READY") return "green";
  if (value === "DEGRADED" || value === "PARTIAL") return "amber";
  if (value === "FAILED") return "red";
  return "neutral";
}

export function DeploymentPanel() {
  const versionQuery = useSystemVersionQuery();
  const validateMutation = useSystemValidateMutation();
  const releaseCheckMutation = useSystemReleaseCheckMutation();
  const [validation, setValidation] = useState<SystemValidationResult | null>(
    null,
  );
  const [releaseCheck, setReleaseCheck] = useState<SystemReleaseCheck | null>(
    null,
  );

  if (versionQuery.isLoading) {
    return <LoadingState label="Loading deployment status" />;
  }
  if (versionQuery.isError) {
    return (
      <ErrorState
        description="Unable to load deployment version information."
        title="Deployment unavailable"
      />
    );
  }

  const version = versionQuery.data?.data;

  return (
    <Panel
      description="Operational validation and release gate checks for production readiness."
      title="Deployment"
    >
      <div className="space-y-4 p-4">
        {version ? (
          <div className="flex flex-wrap gap-2">
            <Badge tone="neutral">{version.service}</Badge>
            <Badge tone="green">v{version.application_version}</Badge>
            <Badge tone="neutral">{version.environment}</Badge>
            <Badge tone="neutral">engine {version.engine_version}</Badge>
          </div>
        ) : (
          <EmptyState
            description="Version endpoint returned no payload."
            title="No version"
          />
        )}

        <div className="flex flex-wrap gap-2">
          <Button
            disabled={validateMutation.isPending}
            onClick={() => {
              validateMutation.mutate(undefined, {
                onSuccess: (response) => setValidation(response.data),
              });
            }}
            size="sm"
            variant="secondary"
          >
            <FlaskConical size={14} /> Run validation
          </Button>
          <Button
            disabled={releaseCheckMutation.isPending}
            onClick={() => {
              releaseCheckMutation.mutate(undefined, {
                onSuccess: (response) => setReleaseCheck(response.data),
              });
            }}
            size="sm"
            variant="secondary"
          >
            <ShieldCheck size={14} /> Release check
          </Button>
        </div>

        {validateMutation.isError ? (
          <ErrorState
            description="Operational validation request failed."
            title="Validation error"
          />
        ) : null}
        {releaseCheckMutation.isError ? (
          <ErrorState
            description="Release check request failed."
            title="Release check error"
          />
        ) : null}

        {validation ? (
          <div className="space-y-2 rounded-lg border border-slate-800 p-3">
            <div className="flex items-center justify-between">
              <p className="text-xs font-medium text-slate-300">
                Operational validation
              </p>
              <Badge tone={toneFor(validation.status)}>{validation.status}</Badge>
            </div>
            <p className="text-[11px] text-slate-500">
              {validation.pass_count} pass · {validation.warn_count} warn ·{" "}
              {validation.fail_count} fail
            </p>
            {!validation.checks.length ? (
              <EmptyState
                description="Validation completed with no check rows."
                title="No checks"
              />
            ) : (
              <ul className="max-h-48 space-y-1 overflow-y-auto text-xs text-slate-400">
                {validation.checks.map((item) => (
                  <li key={item.check}>
                    <span className="text-slate-300">{item.check}</span>:{" "}
                    {item.status} — {item.message}
                  </li>
                ))}
              </ul>
            )}
          </div>
        ) : null}

        {releaseCheck ? (
          <div className="space-y-2 rounded-lg border border-slate-800 p-3">
            <div className="flex items-center justify-between">
              <p className="text-xs font-medium text-slate-300">Release check</p>
              <Badge tone={toneFor(releaseCheck.status)}>
                {releaseCheck.status}
              </Badge>
            </div>
            <p className="text-[11px] text-slate-500">
              Backup records: {releaseCheck.backup_records.length} · Restore:{" "}
              {String(
                (releaseCheck.restore as { status?: string }).status ?? "—",
              )}
            </p>
          </div>
        ) : null}
      </div>
    </Panel>
  );
}
