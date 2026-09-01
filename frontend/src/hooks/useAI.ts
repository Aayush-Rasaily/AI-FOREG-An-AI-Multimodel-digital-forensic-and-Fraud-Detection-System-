import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { aiService } from "../services/api/ai";

export function useAIModelsQuery() {
  return useQuery({
    queryKey: ["ai", "models"],
    queryFn: () => aiService.listModels(),
    staleTime: 10_000,
  });
}

export function useInferenceJobsQuery() {
  return useQuery({
    queryKey: ["ai", "inference-jobs"],
    queryFn: () => aiService.listJobs(),
    staleTime: 10_000,
  });
}

export function useReloadModelMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (modelName: string) => aiService.reloadModel(modelName),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["ai", "models"] });
      void queryClient.invalidateQueries({ queryKey: ["ai", "inference-jobs"] });
    },
  });
}
