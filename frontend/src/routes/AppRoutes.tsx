import { lazy, Suspense } from "react";
import { Navigate, Outlet, Route, Routes } from "react-router-dom";

import { AppShell } from "../layouts/AppShell";
import { LoadingState } from "../components/ui/LoadingState";

const DashboardPage = lazy(() => import("../pages/DashboardPage").then((module) => ({ default: module.DashboardPage })));
const EvidencePage = lazy(() => import("../pages/EvidencePage").then((module) => ({ default: module.EvidencePage })));
const InvestigationWorkspacePage = lazy(() =>
  import("../pages/InvestigationWorkspacePage").then((module) => ({
    default: module.InvestigationWorkspacePage,
  })),
);
const InvestigationsPage = lazy(() =>
  import("../pages/InvestigationsPage").then((module) => ({ default: module.InvestigationsPage })),
);
const NotFoundPage = lazy(() => import("../pages/NotFoundPage").then((module) => ({ default: module.NotFoundPage })));
const ReportsPage = lazy(() => import("../pages/ReportsPage").then((module) => ({ default: module.ReportsPage })));
const SettingsPage = lazy(() => import("../pages/SettingsPage").then((module) => ({ default: module.SettingsPage })));
const SystemPage = lazy(() => import("../pages/SystemPage").then((module) => ({ default: module.SystemPage })));

function ShellRoute() {
  return (
    <AppShell>
      <Outlet />
    </AppShell>
  );
}

export function AppRoutes() {
  return (
    <Suspense fallback={<LoadingState label="Loading workspace" />}>
      <Routes>
        <Route element={<ShellRoute />}>
          <Route element={<Navigate replace to="/dashboard" />} path="/" />
          <Route element={<DashboardPage />} path="/dashboard" />
          <Route element={<InvestigationsPage />} path="/investigations" />
          <Route element={<InvestigationWorkspacePage />} path="/investigations/:caseId" />
          <Route element={<EvidencePage />} path="/evidence" />
          <Route element={<ReportsPage />} path="/reports" />
          <Route element={<SettingsPage />} path="/settings" />
          <Route element={<SystemPage />} path="/system" />
          <Route element={<NotFoundPage />} path="*" />
        </Route>
      </Routes>
    </Suspense>
  );
}

