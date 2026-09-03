import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { auditService } from "../services/api/audit";

export function useAuditEventsQuery(
  caseId: string,
  limit = 50,
  offset = 0,
) {
  return useQuery({
    queryKey: ["case", caseId, "audit", limit, offset],
    queryFn: () => auditService.listForCase(caseId, limit, offset),
    enabled: Boolean(caseId),
    staleTime: 10_000,
  });
}

export function useIntegrityVerifyMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: {
      case_id?: string;
      evidence_id?: string;
      report_id?: string;
    }) => auditService.verify(params),
    onSuccess: (_data, variables) => {
      if (variables.case_id) {
        void queryClient.invalidateQueries({
          queryKey: ["case", variables.case_id, "audit"],
        });
      }
    },
  });
}
