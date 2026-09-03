import { apiClient } from "./client";
import type { ApiResponse } from "../../types/api";
import type {
  AuthUser,
  LoginPayload,
  PermissionInfo,
  RoleInfo,
  SessionList,
  TokenPair,
  UserCreatePayload,
  UserList,
  UserUpdatePayload,
} from "../../types/auth";

export const authApi = {
  login(payload: LoginPayload) {
    return apiClient.postJson<ApiResponse<TokenPair>>("/auth/login", payload);
  },
  refresh(refreshToken: string) {
    return apiClient.postJson<ApiResponse<TokenPair>>("/auth/refresh", {
      refresh_token: refreshToken,
    });
  },
  logout(refreshToken?: string | null) {
    return apiClient.postJson<ApiResponse<{ revoked: boolean }>>("/auth/logout", {
      refresh_token: refreshToken ?? null,
    });
  },
  me() {
    return apiClient.get<ApiResponse<AuthUser>>("/auth/me");
  },
  changePassword(currentPassword: string, newPassword: string) {
    return apiClient.postJson<ApiResponse<{ updated: boolean }>>("/auth/password", {
      current_password: currentPassword,
      new_password: newPassword,
    });
  },
  listUsers(limit = 50, offset = 0) {
    return apiClient.get<ApiResponse<UserList>>(
      `/users?limit=${limit}&offset=${offset}`,
    );
  },
  createUser(payload: UserCreatePayload) {
    return apiClient.postJson<ApiResponse<AuthUser>>("/users", payload);
  },
  updateUser(userId: string, payload: UserUpdatePayload) {
    return apiClient.patchJson<ApiResponse<AuthUser>>(`/users/${userId}`, payload);
  },
  deleteUser(userId: string) {
    return apiClient.deleteJson<ApiResponse<{ deactivated: boolean }>>(
      `/users/${userId}`,
    );
  },
  listRoles() {
    return apiClient.get<ApiResponse<RoleInfo[]>>("/roles");
  },
  listPermissions() {
    return apiClient.get<ApiResponse<PermissionInfo[]>>("/permissions");
  },
  listSessions(allUsers = false) {
    return apiClient.get<ApiResponse<SessionList>>(
      `/sessions?all_users=${allUsers ? "true" : "false"}`,
    );
  },
  revokeSession(sessionId: string) {
    return apiClient.deleteJson<ApiResponse<{ revoked: boolean }>>(
      `/sessions/${sessionId}`,
    );
  },
  revokeAllSessions() {
    return apiClient.deleteJson<ApiResponse<{ revoked: boolean }>>("/sessions");
  },
};
