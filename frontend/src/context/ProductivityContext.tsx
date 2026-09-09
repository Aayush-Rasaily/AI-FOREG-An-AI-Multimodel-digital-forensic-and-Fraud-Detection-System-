import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useNavigate } from "react-router-dom";

import {
  PREF_KEYS,
  pushNotificationLog,
  touchRecentCase,
  useLocalJsonState,
  type NotificationRecord,
  type OpenInvestigationTab,
  type PreferredView,
} from "../hooks/useInvestigatorPreferences";
import { useToast } from "../components/ui/Toast";

export type CommandPaletteMode = "commands" | "search" | "help";

interface ProductivityContextValue {
  commandOpen: boolean;
  commandMode: CommandPaletteMode;
  openCommandPalette: (mode?: CommandPaletteMode) => void;
  closeCommandPalette: () => void;

  notificationOpen: boolean;
  setNotificationOpen: (open: boolean) => void;
  notifications: NotificationRecord[];
  unreadCount: number;
  notify: (
    input: Omit<NotificationRecord, "id" | "createdAt" | "read">,
  ) => void;
  markAllNotificationsRead: () => void;
  clearNotifications: () => void;

  openTabs: OpenInvestigationTab[];
  openInvestigation: (tab: OpenInvestigationTab) => void;
  registerOpenTab: (tab: OpenInvestigationTab) => void;
  closeInvestigationTab: (caseId: string) => void;
  markTabDirty: (caseId: string, dirty: boolean) => void;

  recentCases: Array<{ id: string; title: string; caseNumber: string }>;
  pinnedCaseIds: string[];
  favoriteCaseIds: string[];
  togglePinned: (caseId: string) => void;
  toggleFavorite: (caseId: string) => void;
  recordRecent: (item: {
    id: string;
    title: string;
    caseNumber: string;
  }) => void;

  preferredView: PreferredView;
  setPreferredView: (view: PreferredView) => void;

  sidebarCollapsedPref: boolean | null;
  setSidebarCollapsedPref: (value: boolean) => void;

  panelSizes: Record<string, number>;
  setPanelSize: (key: string, width: number) => void;

  pinnedPanels: string[];
  togglePinnedPanel: (panelId: string) => void;

  activeTabByCase: Record<string, string>;
  setCaseActiveTab: (caseId: string, tab: string) => void;

  navigateShortcut: (path: string) => void;
}

const ProductivityContext = createContext<ProductivityContextValue | null>(
  null,
);

export function ProductivityProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const toast = useToast();

  const [commandOpen, setCommandOpen] = useState(false);
  const [commandMode, setCommandMode] =
    useState<CommandPaletteMode>("commands");
  const [notificationOpen, setNotificationOpen] = useState(false);

  const [openTabs, setOpenTabs] = useLocalJsonState<OpenInvestigationTab[]>(
    PREF_KEYS.openInvestigationTabs,
    [],
  );
  const [recentCases, setRecentCases] = useLocalJsonState<
    Array<{ id: string; title: string; caseNumber: string }>
  >(PREF_KEYS.recentCases, []);
  const [pinnedCaseIds, setPinnedCaseIds] = useLocalJsonState<string[]>(
    PREF_KEYS.pinnedCases,
    [],
  );
  const [favoriteCaseIds, setFavoriteCaseIds] = useLocalJsonState<string[]>(
    PREF_KEYS.favoriteCases,
    [],
  );
  const [notifications, setNotifications] = useLocalJsonState<
    NotificationRecord[]
  >(PREF_KEYS.notifications, []);
  const [preferredView, setPreferredView] = useLocalJsonState<PreferredView>(
    PREF_KEYS.preferredView,
    "overview",
  );
  const [sidebarCollapsedPref, setSidebarCollapsedPref] = useLocalJsonState<
    boolean | null
  >(PREF_KEYS.sidebarCollapsed, null);
  const [panelSizes, setPanelSizes] = useLocalJsonState<Record<string, number>>(
    PREF_KEYS.panelSizes,
    {},
  );
  const [pinnedPanels, setPinnedPanels] = useLocalJsonState<string[]>(
    PREF_KEYS.pinnedPanels,
    [],
  );
  const [activeTabByCase, setActiveTabByCase] = useLocalJsonState<
    Record<string, string>
  >(PREF_KEYS.activeTabByCase, {});

  const openCommandPalette = useCallback((mode: CommandPaletteMode = "commands") => {
    setCommandMode(mode);
    setCommandOpen(true);
  }, []);

  const closeCommandPalette = useCallback(() => {
    setCommandOpen(false);
  }, []);

  const notify = useCallback(
    (input: Omit<NotificationRecord, "id" | "createdAt" | "read">) => {
      try {
        const jobsEnabled =
          localStorage.getItem(PREF_KEYS.notifyJobs) !== "false";
        const systemEnabled =
          localStorage.getItem(PREF_KEYS.notifySystem) !== "false";
        if (input.category === "job" || input.category === "processing") {
          if (!jobsEnabled) return;
        }
        if (input.category === "system" && !systemEnabled) {
          return;
        }
      } catch {
        /* ignore preference read failures */
      }
      setNotifications((current) => pushNotificationLog(current, input));
      toast.push({
        title: input.title,
        description: input.description,
        tone: input.tone,
      });
    },
    [setNotifications, toast],
  );

  const markAllNotificationsRead = useCallback(() => {
    setNotifications((current) =>
      current.map((item) => ({ ...item, read: true })),
    );
  }, [setNotifications]);

  const clearNotifications = useCallback(() => {
    setNotifications([]);
  }, [setNotifications]);

  const registerOpenTab = useCallback(
    (tab: OpenInvestigationTab) => {
      setOpenTabs((current) => {
        if (current.some((item) => item.caseId === tab.caseId)) {
          return current.map((item) =>
            item.caseId === tab.caseId ? { ...item, ...tab } : item,
          );
        }
        return [...current, tab].slice(-8);
      });
      setRecentCases((current) =>
        touchRecentCase(current, {
          id: tab.caseId,
          title: tab.title,
          caseNumber: tab.caseNumber,
        }),
      );
    },
    [setOpenTabs, setRecentCases],
  );

  const openInvestigation = useCallback(
    (tab: OpenInvestigationTab) => {
      registerOpenTab(tab);
      navigate(`/investigations/${tab.caseId}`);
    },
    [navigate, registerOpenTab],
  );

  const closeInvestigationTab = useCallback(
    (caseId: string) => {
      setOpenTabs((current) => {
        const next = current.filter((item) => item.caseId !== caseId);
        return next;
      });
    },
    [setOpenTabs],
  );

  const markTabDirty = useCallback(
    (caseId: string, dirty: boolean) => {
      setOpenTabs((current) =>
        current.map((item) =>
          item.caseId === caseId ? { ...item, dirty } : item,
        ),
      );
    },
    [setOpenTabs],
  );

  const togglePinned = useCallback(
    (caseId: string) => {
      setPinnedCaseIds((current) =>
        current.includes(caseId)
          ? current.filter((id) => id !== caseId)
          : [...current, caseId],
      );
    },
    [setPinnedCaseIds],
  );

  const toggleFavorite = useCallback(
    (caseId: string) => {
      setFavoriteCaseIds((current) =>
        current.includes(caseId)
          ? current.filter((id) => id !== caseId)
          : [...current, caseId],
      );
    },
    [setFavoriteCaseIds],
  );

  const recordRecent = useCallback(
    (item: { id: string; title: string; caseNumber: string }) => {
      setRecentCases((current) => touchRecentCase(current, item));
    },
    [setRecentCases],
  );

  const setPanelSize = useCallback(
    (key: string, width: number) => {
      setPanelSizes((current) => ({ ...current, [key]: width }));
    },
    [setPanelSizes],
  );

  const togglePinnedPanel = useCallback(
    (panelId: string) => {
      setPinnedPanels((current) =>
        current.includes(panelId)
          ? current.filter((id) => id !== panelId)
          : [...current, panelId],
      );
    },
    [setPinnedPanels],
  );

  const setCaseActiveTab = useCallback(
    (caseId: string, tab: string) => {
      setActiveTabByCase((current) => ({ ...current, [caseId]: tab }));
    },
    [setActiveTabByCase],
  );

  const navigateShortcut = useCallback(
    (path: string) => {
      navigate(path);
      setCommandOpen(false);
    },
    [navigate],
  );

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      const typing =
        target &&
        (target.tagName === "INPUT" ||
          target.tagName === "TEXTAREA" ||
          target.isContentEditable);

      if (event.key === "Escape") {
        setCommandOpen(false);
        setNotificationOpen(false);
        return;
      }

      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setCommandMode("commands");
        setCommandOpen((open) => !open);
        return;
      }

      if (typing) {
        return;
      }

      if ((event.ctrlKey || event.metaKey) && event.shiftKey) {
        const key = event.key.toLowerCase();
        if (key === "f") {
          event.preventDefault();
          navigate("/investigations");
          notify({
            title: "Fusion shortcut",
            description: "Open a case workspace, then switch to Correlations / Forensics for fusion views.",
            tone: "info",
            category: "system",
          });
        }
        if (key === "r") {
          event.preventDefault();
          navigate("/reports");
        }
      }

      if ((event.ctrlKey || event.metaKey) && event.key === "/") {
        event.preventDefault();
        setCommandMode("help");
        setCommandOpen(true);
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [navigate, notify]);

  const unreadCount = notifications.filter((item) => !item.read).length;

  const value = useMemo(
    () => ({
      commandOpen,
      commandMode,
      openCommandPalette,
      closeCommandPalette,
      notificationOpen,
      setNotificationOpen,
      notifications,
      unreadCount,
      notify,
      markAllNotificationsRead,
      clearNotifications,
      openTabs,
      openInvestigation,
      registerOpenTab,
      closeInvestigationTab,
      markTabDirty,
      recentCases,
      pinnedCaseIds,
      favoriteCaseIds,
      togglePinned,
      toggleFavorite,
      recordRecent,
      preferredView,
      setPreferredView,
      sidebarCollapsedPref,
      setSidebarCollapsedPref,
      panelSizes,
      setPanelSize,
      pinnedPanels,
      togglePinnedPanel,
      activeTabByCase,
      setCaseActiveTab,
      navigateShortcut,
    }),
    [
      activeTabByCase,
      clearNotifications,
      closeCommandPalette,
      closeInvestigationTab,
      commandMode,
      commandOpen,
      favoriteCaseIds,
      markAllNotificationsRead,
      markTabDirty,
      navigateShortcut,
      notificationOpen,
      notifications,
      notify,
      openCommandPalette,
      openInvestigation,
      openTabs,
      registerOpenTab,
      panelSizes,
      pinnedCaseIds,
      pinnedPanels,
      preferredView,
      recentCases,
      recordRecent,
      setCaseActiveTab,
      setPanelSize,
      setPreferredView,
      setSidebarCollapsedPref,
      sidebarCollapsedPref,
      toggleFavorite,
      togglePinned,
      togglePinnedPanel,
      unreadCount,
    ],
  );

  return (
    <ProductivityContext.Provider value={value}>
      {children}
    </ProductivityContext.Provider>
  );
}

export function useProductivity(): ProductivityContextValue {
  const value = useContext(ProductivityContext);
  if (!value) {
    throw new Error("useProductivity must be used within ProductivityProvider");
  }
  return value;
}

export function useOptionalProductivity(): ProductivityContextValue | null {
  return useContext(ProductivityContext);
}
