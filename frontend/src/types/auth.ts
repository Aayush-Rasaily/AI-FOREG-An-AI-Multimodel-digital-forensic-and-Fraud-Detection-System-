export type AuthRole =
  | "Administrator"
  | "Investigator"
  | "Analyst"
  | "Reviewer"
  | "Viewer";

export interface AuthUser {
  id: string;
  username: string;
  display_name: string;
  email: string | null;
  is_active: boolean;
  is_locked: boolean;
  roles: string[];
  permissions: string[];
  last_login_at: string | null;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: AuthUser;
}

export interface LoginPayload {
  username: string;
  password: string;
  remember_me?: boolean;
}

export interface UserCreatePayload {
  username: string;
  password: string;
  display_name: string;
  email?: string | null;
  role_names: string[];
  is_active?: boolean;
}

export interface UserUpdatePayload {
  display_name?: string;
  email?: string | null;
  is_active?: boolean;
  role_names?: string[];
}

export interface RoleInfo {
  id: string;
  name: string;
  description: string;
  is_system: boolean;
  permissions: string[];
}

export interface PermissionInfo {
  code: string;
  description: string;
}

export interface SessionInfo {
  id: string;
  user_id: string;
  created_at: string;
  last_activity_at: string;
  expires_at: string;
  device_name: string | null;
  browser: string | null;
  ip_address: string | null;
  remember_me: boolean;
  revoked: boolean;
  current: boolean;
}

export interface UserList {
  items: AuthUser[];
  total: number;
  limit: number;
  offset: number;
}

export interface SessionList {
  items: SessionInfo[];
  total: number;
}
