import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { evidenceService } from "../services/api/evidence";

export function useCaseEvidenceQuery(caseId: string | undefined) {
  return useQuery({
    enabled: Boolean(caseId),
    queryKey: ["cases", caseId, "evidence"],
    queryFn: () => evidenceService.listForCase(caseId as string),
    staleTime: 15_000,
  });
}

export function useUploadEvidenceMutation(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => evidenceService.upload(caseId, file),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ["cases", caseId, "evidence"],
      });
      void queryClient.invalidateQueries({ queryKey: ["cases", caseId] });
      void queryClient.invalidateQueries({ queryKey: ["cases"] });
    },
  });
}
