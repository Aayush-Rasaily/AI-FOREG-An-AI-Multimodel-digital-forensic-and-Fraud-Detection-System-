import { Navigate } from "react-router-dom";

import { useWorkspacePreferences } from "../../hooks/useWorkspacePreferences";

/** Honors the locally persisted default dashboard preference. */
export function DefaultHomeRedirect() {
  const { defaultDashboard } = useWorkspacePreferences();
  return <Navigate replace to={defaultDashboard || "/dashboard"} />;
}
