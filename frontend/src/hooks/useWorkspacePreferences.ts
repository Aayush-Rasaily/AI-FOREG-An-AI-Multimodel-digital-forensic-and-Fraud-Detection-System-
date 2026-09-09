import {
  PREF_KEYS,
  useLocalJsonState,
  type DefaultDashboardPath,
  type SidebarBehavior,
} from "./useInvestigatorPreferences";

export function useWorkspacePreferences() {
  const [defaultDashboard, setDefaultDashboard] =
    useLocalJsonState<DefaultDashboardPath>(
      PREF_KEYS.defaultDashboard,
      "/dashboard",
    );
  const [notifyJobs, setNotifyJobs] = useLocalJsonState<boolean>(
    PREF_KEYS.notifyJobs,
    true,
  );
  const [notifySystem, setNotifySystem] = useLocalJsonState<boolean>(
    PREF_KEYS.notifySystem,
    true,
  );
  const [onboardingDismissed, setOnboardingDismissed] = useLocalJsonState<boolean>(
    PREF_KEYS.onboardingDismissed,
    true,
  );
  const [sidebarBehavior, setSidebarBehavior] =
    useLocalJsonState<SidebarBehavior>(PREF_KEYS.sidebarBehavior, "auto");

  return {
    defaultDashboard,
    setDefaultDashboard,
    notifyJobs,
    setNotifyJobs,
    notifySystem,
    setNotifySystem,
    onboardingDismissed,
    setOnboardingDismissed,
    sidebarBehavior,
    setSidebarBehavior,
  };
}
