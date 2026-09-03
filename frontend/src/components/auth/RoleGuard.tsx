import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { useAuth } from "../../context/AuthContext";
import { LoadingState } from "../ui/LoadingState";

interface RoleGuardProps {
  children: ReactNode;
  permission?: string;
  role?: string;
  fallback?: ReactNode;
}

export function RoleGuard({
  children,
  permission,
  role,
  fallback,
}: RoleGuardProps) {
  const { hasPermission, hasRole, loading } = useAuth();
  if (loading) {
    return <LoadingState label="Checking permissions" />;
  }
  const allowed =
    (permission ? hasPermission(permission) : true) &&
    (role ? hasRole(role) : true);

  if (!allowed) {
    return fallback ?? <Navigate replace to="/unauthorized" />;
  }

  return children;
}
