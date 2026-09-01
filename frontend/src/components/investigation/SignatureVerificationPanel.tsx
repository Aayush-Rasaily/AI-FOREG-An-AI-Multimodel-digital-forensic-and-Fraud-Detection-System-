import { useState } from "react";
import { PenLine, ShieldCheck } from "lucide-react";

import {
  useQueueSignatureAnalysisMutation,
  useSignatureAnalysisQuery,
} from "../../hooks/useSignatureAI";
import type { EvidenceRecord } from "../../types/evidence";
import { ApiClientError } from "../../services/api/client";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";
import { Select } from "../ui/Select";

interface SignatureVerificationPanelProps {
  evidence?: EvidenceRecord;
  referenceOptions?: EvidenceRecord[];
}

const verdictTone: Record<
  string,
  "neutral" | "cyan" | "green" | "amber" | "red"
> = {
  MATCH: "green",
  NON_MATCH: "red",
  INCONCLUSIVE: "amber",
  UNAVAILABLE: "neutral",
};

export function SignatureVerificationPanel({
  evidence,
  referenceOptions = [],
}: SignatureVerificationPanelProps) {
  const evidenceId = evidence?.id ?? "";
  const runsQuery = useSignatureAnalysisQuery(evidenceId);
  const queueMutation = useQueueSignatureAnalysisMutation();
  const [referenceEvidenceId, setReferenceEvidenceId] = useState("");
  const latestRun = runsQuery.data?.data.items[0];
  const selectableReferences = referenceOptions.filter(
    (item) => item.id !== evidence?.id,
  );

  return (
    <Panel
      description="Siamese signature verification with hash preservation and model provenance."
      title="Signature Verification"
    >
      <div className="space-y-3 p-4">
        {!evidence && (
          <EmptyState
            description="Select questioned evidence to verify a signature."
            title="No evidence selected"
          />
        )}

        {evidence && (
          <>
            <div className="space-y-2">
              <label
                className="text-[11px] text-slate-500"
                htmlFor="signature-reference"
              >
                Reference signature evidence
              </label>
              <Select
                id="signature-reference"
                onChange={(event) => setReferenceEvidenceId(event.target.value)}
                value={referenceEvidenceId}
              >
                <option value="">Select reference evidence</option>
                {selectableReferences.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.original_filename} ({item.evidence_number})
                  </option>
                ))}
              </Select>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <Button
                disabled={
                  !referenceEvidenceId ||
                  queueMutation.isPending ||
                  evidence.id === referenceEvidenceId
                }
                onClick={() =>
                  queueMutation.mutate({
                    questionedEvidenceId: evidence.id,
                    referenceEvidenceId,
                  })
                }
                size="sm"
              >
                <PenLine aria-hidden="true" size={14} />
                Queue signature verification
              </Button>
              {latestRun && (
                <Badge tone={verdictTone[latestRun.verdict] ?? "neutral"}>
                  {latestRun.verdict}
                </Badge>
              )}
            </div>

            {runsQuery.isPending && (
              <LoadingState label="Loading signature verification runs" />
            )}
            {runsQuery.isError && (
              <ErrorState
                description={
                  runsQuery.error instanceof ApiClientError
                    ? runsQuery.error.message
                    : "Signature verification history could not be loaded."
                }
                onRetry={() => void runsQuery.refetch()}
              />
            )}

            {latestRun && (
              <div className="rounded border border-slate-800 px-3 py-2 text-xs text-slate-400">
                <div className="flex items-center gap-2">
                  <ShieldCheck aria-hidden="true" size={14} />
                  <span>
                    {latestRun.model} v{latestRun.model_version}
                  </span>
                  {latestRun.similarity != null && (
                    <>
                      <span>·</span>
                      <span>
                        Similarity {(latestRun.similarity * 100).toFixed(1)}%
                      </span>
                    </>
                  )}
                </div>
                <p className="mt-2 break-all text-[10px] text-slate-600">
                  Reference hash: {latestRun.reference_hash}
                </p>
                <p className="mt-1 break-all text-[10px] text-slate-600">
                  Questioned hash: {latestRun.questioned_hash}
                </p>
                {latestRun.verdict === "UNAVAILABLE" && (
                  <p className="mt-2 text-[11px] text-amber-300">
                    Signature model is unavailable. Configure SIGNATURE_MODEL_PATH to
                    enable inference.
                  </p>
                )}
              </div>
            )}

            {runsQuery.isSuccess &&
              (runsQuery.data?.data.items.length ?? 0) === 0 && (
                <EmptyState
                  description="Queue signature verification against trusted reference evidence."
                  title="No signature verification runs"
                />
              )}

            {queueMutation.isError && (
              <p className="text-[11px] text-red-300">
                {queueMutation.error instanceof ApiClientError
                  ? queueMutation.error.message
                  : "Signature verification failed."}
              </p>
            )}
          </>
        )}
      </div>
    </Panel>
  );
}
