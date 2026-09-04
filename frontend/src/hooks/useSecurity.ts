import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { securityApi } from "../services/api/security";

export function useSecurityRolesQuery() {
  return useQuery({
    queryKey: ["security", "roles"],
    queryFn: () => securityApi.listRoles(),
  });
}

export function useSecurityPermissionsQuery() {
  return useQuery({
    queryKey: ["security", "permissions"],
    queryFn: () => securityApi.listPermissions(),
  });
}

export function useSecurityPolicyQuery() {
  return useQuery({
    queryKey: ["security", "policy"],
    queryFn: () => securityApi.getPolicy(),
  });
}

export function useSecurityViolationsQuery(caseId?: string) {
  return useQuery({
    queryKey: ["security", "violations", caseId ?? "all"],
    queryFn: () => securityApi.listViolations(caseId),
  });
}

export function useCaseAccessQuery(caseId: string) {
  return useQuery({
    queryKey: ["case", caseId, "access"],
    queryFn: () => securityApi.listCaseAccess(caseId),
    enabled: Boolean(caseId),
  });
}

export function useCaseComplianceQuery(caseId: string) {
  return useQuery({
    queryKey: ["case", caseId, "compliance"],
    queryFn: () => securityApi.getCompliance(caseId),
    enabled: Boolean(caseId),
  });
}

export function useSecurityValidateMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (caseId?: string | null) => securityApi.validate(caseId),
    onSuccess: async (_data, caseId) => {
      await queryClient.invalidateQueries({
        queryKey: ["security", "violations"],
      });
      if (caseId) {
        await queryClient.invalidateQueries({
          queryKey: ["case", caseId, "compliance"],
        });
      }
    },
  });
}
