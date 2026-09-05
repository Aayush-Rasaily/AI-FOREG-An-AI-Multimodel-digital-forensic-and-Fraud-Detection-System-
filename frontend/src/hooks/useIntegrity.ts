import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { integrityApi } from "../services/api/integrity";

export function useIntegrityQuery(caseId: string) {
  return useQuery({
    queryKey: ["integrity", caseId],
    queryFn: () => integrityApi.getLatest(caseId),
    retry: false,
  });
}

export function useRunIntegrityCheckMutation(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => integrityApi.runCheck(caseId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["integrity", caseId] });
    },
  });
}

export function useIntegrityHistoryQuery(caseId: string) {
  return useQuery({
    queryKey: ["integrity", caseId, "history"],
    queryFn: () => integrityApi.getHistory(caseId),
  });
}
