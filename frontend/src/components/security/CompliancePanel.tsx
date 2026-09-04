import {
  useCaseComplianceQuery,
  useSecurityValidateMutation,
} from "../../hooks/useSecurity";
import { Button } from "../ui/Button";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";
import { SecurityStatusBadge } from "./SecurityStatusBadge";

export function CompliancePanel({ caseId }: { caseId: string }) {
  const query = useCaseComplianceQuery(caseId);
  const validate = useSecurityValidateMutation();
  const report = query.data?.data;

  return (
    <Panel
      description="Chain-of-custody, integrity, audit, and approval compliance."
      title="Compliance"
    >
      <div className="space-y-3 p-4">
        <Button
          disabled={validate.isPending}
          onClick={() => void validate.mutateAsync(caseId)}
          size="sm"
          variant="secondary"
        >
          Run chain validation
        </Button>
        {query.isLoading && <LoadingState label="Loading compliance" />}
        {query.isError && (
          <ErrorState
            description="Compliance summary could not be loaded."
            title="Error"
          />
        )}
        {report && (
          <div className="space-y-2 text-sm text-slate-300">
            <SecurityStatusBadge status={report.status} />
            <ul className="space-y-1 text-xs text-slate-500">
              <li>
                Custody complete:{" "}
                {report.chain_of_custody_complete ? "yes" : "no"}
              </li>
              <li>
                Evidence integrity:{" "}
                {report.evidence_integrity_ok ? "ok" : "gaps"}
              </li>
              <li>Audit complete: {report.audit_complete ? "yes" : "no"}</li>
              <li>
                Workflow compliant: {report.workflow_compliant ? "yes" : "no"}
              </li>
              <li>
                Report approvals:{" "}
                {report.report_approval_compliant ? "ok" : "issues"}
              </li>
            </ul>
            {report.missing_approvals.length > 0 && (
              <p className="text-xs text-amber-400">
                Missing approvals: {report.missing_approvals.join(", ")}
              </p>
            )}
            {report.missing_provenance.length > 0 && (
              <p className="text-xs text-amber-400">
                Missing provenance: {report.missing_provenance.join(", ")}
              </p>
            )}
          </div>
        )}
      </div>
    </Panel>
  );
}
