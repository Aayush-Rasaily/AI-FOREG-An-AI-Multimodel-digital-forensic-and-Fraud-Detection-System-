import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { evidenceService } from "../services/api/evidence";
import { processingService } from "../services/api/processing";
import { extractionService } from "../services/api/extraction";

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

export function useEvidenceProcessingQuery(evidenceId: string) {
  return useQuery({
    queryKey: ["evidence", evidenceId, "processing"],
    queryFn: () => processingService.listJobs(evidenceId),
    refetchInterval: (query) => {
      const latest = query.state.data?.data.items[0];
      return latest?.status === "QUEUED" || latest?.status === "RUNNING"
        ? 1000
        : false;
    },
  });
}

export function useEvidenceArtifactsQuery(evidenceId: string) {
  return useQuery({
    queryKey: ["evidence", evidenceId, "artifacts"],
    queryFn: () => processingService.listArtifacts(evidenceId),
    staleTime: 15_000,
  });
}

export function useProcessEvidenceMutation(evidenceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => processingService.process(evidenceId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ["evidence", evidenceId, "processing"],
      });
      void queryClient.invalidateQueries({
        queryKey: ["evidence", evidenceId, "artifacts"],
      });
      void queryClient.invalidateQueries({
        queryKey: ["cases"],
      });
    },
  });
}

export function useEvidenceExtractionsQuery(evidenceId: string) {
  return useQuery({
    queryKey: ["evidence", evidenceId, "extractions"],
    queryFn: () => extractionService.list(evidenceId),
    refetchInterval: (query) => {
      return query.state.data?.data.error_code === "EXTRACTION_IN_PROGRESS"
        ? 1000
        : false;
    },
  });
}

export function useEvidenceExtractionArtifactsQuery(evidenceId: string) {
  return useQuery({
    queryKey: ["evidence", evidenceId, "extraction-artifacts"],
    queryFn: () => extractionService.artifacts(evidenceId),
    staleTime: 15_000,
  });
}

export function useEvidenceRegionsQuery(evidenceId: string) {
  return useQuery({
    queryKey: ["evidence", evidenceId, "regions"],
    queryFn: () => extractionService.regions(evidenceId),
    staleTime: 15_000,
  });
}

export function useExtractEvidenceMutation(evidenceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => extractionService.extract(evidenceId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ["evidence", evidenceId, "extractions"],
      });
      void queryClient.invalidateQueries({
        queryKey: ["evidence", evidenceId, "extraction-artifacts"],
      });
      void queryClient.invalidateQueries({
        queryKey: ["evidence", evidenceId, "regions"],
      });
      void queryClient.invalidateQueries({
        queryKey: ["evidence", evidenceId, "processing"],
      });
    },
  });
}
