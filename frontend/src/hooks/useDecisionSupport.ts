import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { decisionSupportApi } from "../services/api/decisionSupport";

export function useDecisionSupportQuery(caseId: string) {
  return useQuery({
    queryKey: ["decision-support", caseId],
    queryFn: () => decisionSupportApi.getLatest(caseId),
    retry: false,
  });
}

export function useGenerateDecisionSupportMutation(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => decisionSupportApi.generate(caseId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["decision-support", caseId],
      });
    },
  });
}

export function useDecisionSupportDecisionsQuery(caseId: string) {
  return useQuery({
    queryKey: ["decision-support", caseId, "decisions"],
    queryFn: () => decisionSupportApi.listDecisions(caseId),
  });
}

export function useCreateDecisionMutation(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: {
      decision_type: string;
      investigator: string;
      justification: string;
      task_id?: string;
    }) =>
      decisionSupportApi.createDecision({
        case_id: caseId,
        ...body,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["decision-support", caseId],
      });
    },
  });
}

export function useUpdateWorkflowTaskMutation(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      taskId,
      status,
    }: {
      taskId: string;
      status: string;
    }) => decisionSupportApi.updateTask(taskId, { status }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["decision-support", caseId],
      });
    },
  });
}
