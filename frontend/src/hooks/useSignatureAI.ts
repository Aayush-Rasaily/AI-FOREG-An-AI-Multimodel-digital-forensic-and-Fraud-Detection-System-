import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { signatureAiService } from "../services/api/signatureAi";

export function useSignatureAnalysisQuery(evidenceId: string) {
  return useQuery({
    queryKey: ["evidence", evidenceId, "signature-analysis"],
    queryFn: () => signatureAiService.listRuns(evidenceId),
    enabled: Boolean(evidenceId),
    staleTime: 10_000,
    refetchInterval: (query) => {
      const items = query.state.data?.data.items ?? [];
      const active = items.some(
        (item) =>
          item.metadata.status === "queued" ||
          item.metadata.status === "running",
      );
      return active ? 1000 : false;
    },
  });
}

export function useQueueSignatureAnalysisMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      questionedEvidenceId,
      referenceEvidenceId,
    }: {
      questionedEvidenceId: string;
      referenceEvidenceId: string;
    }) =>
      signatureAiService.queueAnalysis(
        questionedEvidenceId,
        referenceEvidenceId,
      ),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({
        queryKey: [
          "evidence",
          variables.questionedEvidenceId,
          "signature-analysis",
        ],
      });
    },
  });
}
