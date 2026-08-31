import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  caseService,
  type CreateCaseInput,
  type UpdateCaseInput,
} from "../services/api/cases";

export function useCasesQuery() {
  return useQuery({
    queryKey: ["cases"],
    queryFn: () => caseService.list(),
    staleTime: 15_000,
  });
}

export function useCaseQuery(caseId: string | undefined) {
  return useQuery({
    enabled: Boolean(caseId),
    queryKey: ["cases", caseId],
    queryFn: () => caseService.get(caseId as string),
    staleTime: 15_000,
  });
}

export function useCreateCaseMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: CreateCaseInput) => caseService.create(input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["cases"] }),
  });
}

export function useUpdateCaseMutation(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: UpdateCaseInput) => caseService.update(caseId, input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["cases"] });
      void queryClient.invalidateQueries({ queryKey: ["cases", caseId] });
    },
  });
}
