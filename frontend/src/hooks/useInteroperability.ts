import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { interoperabilityApi } from "../services/api/interoperability";
import type { ExportRequest } from "../types/interoperability";

export function useExportsQuery(caseId?: string) {
  return useQuery({
    queryKey: ["interop", "exports", caseId ?? "all"],
    queryFn: () => interoperabilityApi.listExports(caseId),
  });
}

export function useImportsQuery() {
  return useQuery({
    queryKey: ["interop", "imports"],
    queryFn: () => interoperabilityApi.listImports(),
  });
}

export function useExportManifestQuery(exportId: string | null) {
  return useQuery({
    queryKey: ["interop", "manifest", exportId],
    queryFn: () => interoperabilityApi.getManifest(exportId!),
    enabled: Boolean(exportId),
  });
}

export function useExportCaseMutation(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: ExportRequest) =>
      interoperabilityApi.exportCase(caseId, body),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["interop"] });
    },
  });
}

export function useImportPackageMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => interoperabilityApi.importPackage(file),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["interop"] });
    },
  });
}
