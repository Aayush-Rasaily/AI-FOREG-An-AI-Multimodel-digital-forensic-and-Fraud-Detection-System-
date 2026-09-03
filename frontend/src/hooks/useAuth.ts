import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useAuth } from "../context/AuthContext";
import { authApi } from "../services/api/auth";
import type { LoginPayload, UserCreatePayload, UserUpdatePayload } from "../types/auth";

export function useAuthSession() {
  return useAuth();
}

export function useLoginMutation() {
  const { login } = useAuth();
  return useMutation({
    mutationFn: (payload: LoginPayload) => login(payload),
  });
}

export function useUsersQuery(enabled = true) {
  return useQuery({
    queryKey: ["auth", "users"],
    queryFn: async () => (await authApi.listUsers()).data,
    enabled,
  });
}

export function useRolesQuery(enabled = true) {
  return useQuery({
    queryKey: ["auth", "roles"],
    queryFn: async () => (await authApi.listRoles()).data,
    enabled,
  });
}

export function useSessionsQuery(allUsers = false) {
  return useQuery({
    queryKey: ["auth", "sessions", allUsers],
    queryFn: async () => (await authApi.listSessions(allUsers)).data,
  });
}

export function useCreateUserMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: UserCreatePayload) => authApi.createUser(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["auth", "users"] });
    },
  });
}

export function useUpdateUserMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      userId,
      payload,
    }: {
      userId: string;
      payload: UserUpdatePayload;
    }) => authApi.updateUser(userId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["auth", "users"] });
    },
  });
}

export function useDeleteUserMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (userId: string) => authApi.deleteUser(userId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["auth", "users"] });
    },
  });
}

export function useChangePasswordMutation() {
  return useMutation({
    mutationFn: ({
      currentPassword,
      newPassword,
    }: {
      currentPassword: string;
      newPassword: string;
    }) => authApi.changePassword(currentPassword, newPassword),
  });
}

export function useRevokeSessionMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (sessionId: string) => authApi.revokeSession(sessionId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["auth", "sessions"] });
    },
  });
}
