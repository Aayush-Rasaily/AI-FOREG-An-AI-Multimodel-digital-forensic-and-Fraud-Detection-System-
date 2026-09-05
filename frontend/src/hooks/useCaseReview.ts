import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { caseReviewApi } from "../services/api/caseReview";

export function useCaseReviewQuery(caseId: string) {
  return useQuery({
    queryKey: ["case-review", caseId],
    queryFn: () => caseReviewApi.getLatest(caseId),
    retry: false,
  });
}

export function useGenerateCaseReviewMutation(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => caseReviewApi.generate(caseId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["case-review", caseId],
      });
    },
  });
}

export function useCaseReviewHistoryQuery(caseId: string) {
  return useQuery({
    queryKey: ["case-review", caseId, "history"],
    queryFn: () => caseReviewApi.getHistory(caseId),
  });
}

export function useUpdateChecklistItemMutation(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      itemId,
      status,
      notes,
      reviewer,
    }: {
      itemId: string;
      status?: string;
      notes?: string;
      reviewer?: string;
    }) => caseReviewApi.updateChecklistItem(itemId, { status, notes, reviewer }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["case-review", caseId],
      });
    },
  });
}

export function useCreateApprovalMutation(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: {
      reviewer: string;
      approver_role: string;
      decision: string;
      comments?: string;
      run_id?: string;
    }) =>
      caseReviewApi.createApproval({
        case_id: caseId,
        ...body,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["case-review", caseId],
      });
    },
  });
}
