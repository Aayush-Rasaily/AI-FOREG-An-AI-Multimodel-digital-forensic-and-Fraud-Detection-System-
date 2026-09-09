import { useCallback, useEffect, useState } from "react";

import { readJson, writeJson } from "../lib/storage";

export const PREF_KEYS = {
  sidebarCollapsed: "ai-forge-sidebar-collapsed",
  recentCases: "ai-forge-recent-cases",
  pinnedCases: "ai-forge-pinned-cases",
  favoriteCases: "ai-forge-favorite-cases",
  openInvestigationTabs: "ai-forge-open-investigation-tabs",
  activeTabByCase: "ai-forge-case-active-tabs",
  panelSizes: "ai-forge-panel-sizes",
  panelScroll: "ai-forge-panel-scroll",
  preferredView: "ai-forge-preferred-view",
  notifications: "ai-forge-notification-log",
  pinnedPanels: "ai-forge-pinned-panels",
  defaultDashboard: "ai-forge-default-dashboard",
  notifyJobs: "ai-forge-notify-jobs",
  notifySystem: "ai-forge-notify-system",
  onboardingDismissed: "ai-forge-onboarding-dismissed",
  sidebarBehavior: "ai-forge-sidebar-behavior",
} as const;

export type PreferredView = "overview" | "evidence" | "timeline" | "forensics";

export type DefaultDashboardPath =
  | "/dashboard"
  | "/investigations"
  | "/analytics"
  | "/evidence";

export type SidebarBehavior = "auto" | "expanded" | "collapsed";

export interface OpenInvestigationTab {
  caseId: string;
  title: string;
  caseNumber: string;
  dirty?: boolean;
}

export interface NotificationRecord {
  id: string;
  title: string;
  description?: string;
  tone: "info" | "success" | "warning" | "error";
  createdAt: string;
  read: boolean;
  category?: "job" | "processing" | "system" | "general";
}

const MAX_RECENT = 12;
const MAX_NOTIFICATIONS = 40;

export function useLocalJsonState<T>(
  key: string,
  initial: T,
): [T, (value: T | ((current: T) => T)) => void] {
  const [state, setState] = useState<T>(() => readJson(key, initial));

  useEffect(() => {
    writeJson(key, state);
  }, [key, state]);

  const set = useCallback((value: T | ((current: T) => T)) => {
    setState((current) =>
      typeof value === "function" ? (value as (c: T) => T)(current) : value,
    );
  }, []);

  return [state, set];
}

export function touchRecentCase(
  cases: Array<{ id: string; title: string; caseNumber: string }>,
  next: { id: string; title: string; caseNumber: string },
): Array<{ id: string; title: string; caseNumber: string }> {
  const filtered = cases.filter((item) => item.id !== next.id);
  return [next, ...filtered].slice(0, MAX_RECENT);
}

export function pushNotificationLog(
  items: NotificationRecord[],
  next: Omit<NotificationRecord, "id" | "createdAt" | "read">,
): NotificationRecord[] {
  const entry: NotificationRecord = {
    ...next,
    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    createdAt: new Date().toISOString(),
    read: false,
  };
  return [entry, ...items].slice(0, MAX_NOTIFICATIONS);
}
