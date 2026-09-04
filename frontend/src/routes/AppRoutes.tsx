import { lazy, Suspense } from "react";
import { Navigate, Outlet, Route, Routes } from "react-router-dom";

import { ProtectedRoute } from "../components/auth/ProtectedRoute";
import { RoleGuard } from "../components/auth/RoleGuard";
import { LoadingState } from "../components/ui/LoadingState";
import { AppShell } from "../layouts/AppShell";

const DashboardPage = lazy(() =>
  import("../pages/DashboardPage").then((module) => ({ default: module.DashboardPage })),
);
const EvidencePage = lazy(() =>
  import("../pages/EvidencePage").then((module) => ({ default: module.EvidencePage })),
);
const InvestigationWorkspacePage = lazy(() =>
  import("../pages/InvestigationWorkspacePage").then((module) => ({
    default: module.InvestigationWorkspacePage,
  })),
);
const InvestigationsPage = lazy(() =>
  import("../pages/InvestigationsPage").then((module) => ({
    default: module.InvestigationsPage,
  })),
);
const LoginPage = lazy(() =>
  import("../pages/LoginPage").then((module) => ({ default: module.LoginPage })),
);
const NotFoundPage = lazy(() =>
  import("../pages/NotFoundPage").then((module) => ({ default: module.NotFoundPage })),
);
const ProfilePage = lazy(() =>
  import("../pages/ProfilePage").then((module) => ({ default: module.ProfilePage })),
);
const ReportsPage = lazy(() =>
  import("../pages/ReportsPage").then((module) => ({ default: module.ReportsPage })),
);
const SettingsPage = lazy(() =>
  import("../pages/SettingsPage").then((module) => ({ default: module.SettingsPage })),
);
const SystemDashboardPage = lazy(() =>
  import("../pages/SystemDashboardPage").then((module) => ({
    default: module.SystemDashboardPage,
  })),
);
const SystemStatusPage = lazy(() =>
  import("../pages/SystemStatusPage").then((module) => ({
    default: module.SystemStatusPage,
  })),
);
const MonitoringDashboardPage = lazy(() =>
  import("../pages/MonitoringDashboardPage").then((module) => ({
    default: module.MonitoringDashboardPage,
  })),
);
const SecurityGovernancePage = lazy(() =>
  import("../pages/SecurityGovernancePage").then((module) => ({
    default: module.SecurityGovernancePage,
  })),
);
const UnauthorizedPage = lazy(() =>
  import("../pages/UnauthorizedPage").then((module) => ({
    default: module.UnauthorizedPage,
  })),
);
const UserManagementPage = lazy(() =>
  import("../pages/UserManagementPage").then((module) => ({
    default: module.UserManagementPage,
  })),
);
const AIModelsPage = lazy(() =>
  import("../pages/AIModelsPage").then((module) => ({ default: module.AIModelsPage })),
);

function ShellRoute() {
  return (
    <ProtectedRoute>
      <AppShell>
        <Outlet />
      </AppShell>
    </ProtectedRoute>
  );
}

export function AppRoutes() {
  return (
    <Suspense fallback={<LoadingState label="Loading workspace" />}>
      <Routes>
        <Route element={<LoginPage />} path="/login" />
        <Route element={<ShellRoute />}>
          <Route element={<Navigate replace to="/dashboard" />} path="/" />
          <Route element={<DashboardPage />} path="/dashboard" />
          <Route element={<InvestigationsPage />} path="/investigations" />
          <Route
            element={<InvestigationWorkspacePage />}
            path="/investigations/:caseId"
          />
          <Route element={<EvidencePage />} path="/evidence" />
          <Route element={<ReportsPage />} path="/reports" />
          <Route element={<SettingsPage />} path="/settings" />
          <Route element={<ProfilePage />} path="/profile" />
          <Route
            element={
              <RoleGuard permission="system.monitor">
                <SystemDashboardPage />
              </RoleGuard>
            }
            path="/system"
          />
          <Route
            element={
              <RoleGuard permission="system.monitor">
                <SystemStatusPage />
              </RoleGuard>
            }
            path="/deployment"
          />
          <Route
            element={
              <RoleGuard permission="system.monitor">
                <MonitoringDashboardPage />
              </RoleGuard>
            }
            path="/monitoring"
          />
          <Route
            element={
              <RoleGuard permission="admin.manage_users">
                <UserManagementPage />
              </RoleGuard>
            }
            path="/users"
          />
          <Route
            element={
              <RoleGuard permission="security.view">
                <SecurityGovernancePage />
              </RoleGuard>
            }
            path="/security"
          />
          <Route element={<AIModelsPage />} path="/ai-models" />
          <Route element={<UnauthorizedPage />} path="/unauthorized" />
          <Route element={<NotFoundPage />} path="*" />
        </Route>
      </Routes>
    </Suspense>
  );
}
