import {
  AlertTriangle,
  AudioLines,
  BrainCircuit,
  FileSignature,
  Gavel,
  Image,
  ScanText,
  Sparkles,
} from "lucide-react";

import {
  useAnalyzeFusionMutation,
  useFusionConflictsQuery,
  useFusionLatestQuery,
} from "../../hooks/useFusion";
import type { EvidenceRecord } from "../../types/evidence";
import type {
  FusionVerdict,
  JuryAssessment,
  JuryMemberRole,
  ModalityAvailability,
} from "../../types/fusion";
import { ApiClientError } from "../../services/api/client";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";

interface AiJuryPanelProps {
  evidence?: EvidenceRecord;
}

const roleIcons: Record<JuryMemberRole, typeof BrainCircuit> = {
  forensic_analyst: BrainCircuit,
  document_image_specialist: Image,
  multimedia_specialist: AudioLines,
  signature_specialist: FileSignature,
  consistency_analyst: ScanText,
  senior_judge: Gavel,
};

const verdictTone: Record<
  FusionVerdict,
  "neutral" | "primary" | "success" | "warning" | "error"
> = {
  genuine: "success",
  suspicious: "warning",
  potential_fraud: "error",
  inconclusive: "neutral",
  insufficient_evidence: "neutral",
  unavailable: "neutral",
};

const availabilityTone: Record<
  ModalityAvailability,
  "neutral" | "primary" | "success" | "warning" | "error"
> = {
  available: "success",
  unavailable: "neutral",
  not_applicable: "neutral",
  failed: "error",
  insufficient_evidence: "warning",
};

function formatVerdict(value: FusionVerdict | null | undefined): string {
  if (!value) return "—";
  return value.replaceAll("_", " ");
}

function formatPercent(value: number | null | undefined): string {
  if (value == null) return "—";
  return `${Math.round(value * 100)}%`;
}

function JuryMemberCard({ assessment }: { assessment: JuryAssessment }) {
  const Icon = roleIcons[assessment.role] ?? BrainCircuit;
  const unavailable = assessment.availability !== "available";
  return (
    <div className="flex items-start gap-3 rounded-lg border border-border bg-background/50 p-3">
      <Icon aria-hidden="true" className="mt-0.5 shrink-0 text-muted" size={16} />
      <div className="min-w-0 flex-1 space-y-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-medium text-foreground">
            {assessment.member_name}
          </span>
          <Badge tone={unavailable ? "neutral" : verdictTone[assessment.verdict]}>
            {unavailable ? "Unavailable" : formatVerdict(assessment.verdict)}
          </Badge>
        </div>
        <p className="text-[11px] text-muted">{assessment.explanation}</p>
        {!unavailable && assessment.confidence != null && (
          <p className="text-[11px] text-subtle">
            Confidence: {formatPercent(assessment.confidence)}
          </p>
        )}
      </div>
    </div>
  );
}

export function AiJuryPanel({ evidence }: AiJuryPanelProps) {
  const evidenceId = evidence?.id ?? "";
  const latestQuery = useFusionLatestQuery(evidenceId);
  const conflictsQuery = useFusionConflictsQuery(
    evidenceId,
    latestQuery.isSuccess,
  );
  const analyzeMutation = useAnalyzeFusionMutation();

  if (!evidence) {
    return (
      <Panel
        description="Select evidence to run multimodal fusion and AI jury review."
        title="AI Jury"
      >
        <EmptyState
          description="Select evidence to run multimodal fusion and AI jury review."
          title="No evidence selected"
        />
      </Panel>
    );
  }

  const isLoading = latestQuery.isLoading;
  const isNotFound =
    latestQuery.error instanceof ApiClientError && latestQuery.error.status === 404;
  const assessment = latestQuery.data?.data;
  const conflicts = conflictsQuery.data?.data ?? assessment?.conflicts ?? [];
  const isFusionAssessment = Boolean(
    assessment && "engine_version" in assessment && assessment.engine_version,
  );

  return (
    <Panel
      description="Multimodal evidence fusion with independent jury assessments, explicit conflicts, and provenance."
      title="AI Jury"
    >
      <div className="space-y-4 p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="space-y-1">
            <p className="text-xs text-muted">
              Evidence: {evidence.evidence_number ?? evidence.original_filename}
            </p>
            {isFusionAssessment && assessment && (
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone={verdictTone[assessment.verdict ?? "inconclusive"]}>
                  {formatVerdict(assessment.verdict)}
                </Badge>
                {assessment.risk_score != null && (
                  <span className="text-xs text-muted">
                    Risk: {assessment.risk_score}
                  </span>
                )}
                {assessment.confidence != null && (
                  <span className="text-xs text-muted">
                    Confidence: {formatPercent(assessment.confidence)}
                  </span>
                )}
              </div>
            )}
          </div>
          <Button
            disabled={analyzeMutation.isPending}
            onClick={() => analyzeMutation.mutate({ evidenceId })}
            size="sm"
            variant="secondary"
          >
            <Sparkles aria-hidden="true" className="mr-1.5" size={14} />
            {analyzeMutation.isPending ? "Queuing…" : "Run Fusion"}
          </Button>
        </div>

        {isLoading && (
          <LoadingState label="Loading multimodal assessment…" />
        )}

        {!isLoading && latestQuery.isError && !isNotFound && (
          <ErrorState
            description="Unable to load multimodal fusion assessment."
            title="Fusion unavailable"
          />
        )}

        {!isLoading && (isNotFound || !isFusionAssessment) && (
          <EmptyState
            description="Run fusion to aggregate modality findings into a multimodal assessment."
            title="No multimodal fusion analysis yet"
          />
        )}

        {isFusionAssessment && assessment && (
          <>
            {assessment.explanation && (
              <p className="rounded-lg border border-border bg-background/40 p-3 text-xs text-muted">
                {assessment.explanation}
              </p>
            )}

            {assessment.agreement && (
              <div className="grid gap-2 sm:grid-cols-3">
                <div className="rounded-lg border border-border bg-background/40 p-3">
                  <p className="text-[10px] uppercase tracking-wide text-subtle">
                    Jury Agreement
                  </p>
                  <p className="text-sm text-foreground">
                    {assessment.agreement.jury_votes_available}/
                    {assessment.agreement.jury_votes_total}
                  </p>
                </div>
                <div className="rounded-lg border border-border bg-background/40 p-3">
                  <p className="text-[10px] uppercase tracking-wide text-subtle">
                    Supporting Modalities
                  </p>
                  <p className="text-sm text-foreground">
                    {assessment.agreement.supporting_modalities}
                  </p>
                </div>
                <div className="rounded-lg border border-border bg-background/40 p-3">
                  <p className="text-[10px] uppercase tracking-wide text-subtle">
                    Unavailable Modalities
                  </p>
                  <p className="text-sm text-foreground">
                    {assessment.agreement.unavailable_modalities}
                  </p>
                </div>
              </div>
            )}

            {(assessment.modality_status?.length ?? 0) > 0 && (
              <div className="space-y-2">
                <h3 className="text-xs font-medium uppercase tracking-wide text-muted">
                  Modality Status
                </h3>
                <div className="flex flex-wrap gap-2">
                  {assessment.modality_status?.map((status) => (
                    <Badge
                      key={status.modality}
                      tone={availabilityTone[status.availability]}
                    >
                      {status.modality.replaceAll("_", " ")}: {status.availability}
                      {status.findings_count > 0
                        ? ` (${status.findings_count})`
                        : ""}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {(assessment.jury_assessments?.length ?? 0) > 0 && (
              <div className="space-y-2">
                <h3 className="text-xs font-medium uppercase tracking-wide text-muted">
                  Jury Members
                </h3>
                <div className="grid gap-2 sm:grid-cols-2">
                  {assessment.jury_assessments?.map((member) => (
                    <JuryMemberCard
                      assessment={member}
                      key={member.role}
                    />
                  ))}
                </div>
              </div>
            )}

            {conflicts.length > 0 && (
              <div className="space-y-2">
                <h3 className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-warning">
                  <AlertTriangle aria-hidden="true" size={14} />
                  Conflicts
                </h3>
                <div className="space-y-2">
                  {conflicts.map((conflict) => (
                    <div
                      className="rounded-lg border border-warning/40 bg-warning-soft p-3"
                      key={conflict.conflict_id}
                    >
                      <p className="text-xs font-medium text-warning">
                        {conflict.conflict_type.replaceAll("_", " ")}
                      </p>
                      <p className="mt-1 text-[11px] text-warning/85">
                        {conflict.explanation}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {assessment.limitations && (
              <p className="text-[11px] text-subtle">{assessment.limitations}</p>
            )}

            {assessment.provenance?.source_sha256 && (
              <p className="font-mono text-[10px] text-subtle">
                Provenance SHA-256: {String(assessment.provenance.source_sha256)}
              </p>
            )}
          </>
        )}
      </div>
    </Panel>
  );
}
