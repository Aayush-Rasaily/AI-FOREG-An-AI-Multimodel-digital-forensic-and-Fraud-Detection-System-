import { useEffect, useState, type ReactNode } from "react";

import { CommandPalette } from "../components/command/CommandPalette";
import { HelpMenuButton } from "../components/help/HelpChrome";
import { OnboardingWalkthrough } from "../components/help/OnboardingWalkthrough";
import { PageContainer } from "../components/layout/PageContainer";
import { Sidebar } from "../components/navigation/Sidebar";
import { Topbar } from "../components/navigation/Topbar";
import { NotificationCenter } from "../components/notifications/NotificationCenter";
import { OfflineBanner } from "../components/ui/OfflineBanner";
import { useOptionalProductivity } from "../context/ProductivityContext";
import { useViewport } from "../hooks/useMediaQuery";
import { useWorkspacePreferences } from "../hooks/useWorkspacePreferences";

export function AppShell({ children }: { children: ReactNode }) {
  const { isMobile, isTablet, isLaptopUp } = useViewport();
  const productivity = useOptionalProductivity();
  const { sidebarBehavior } = useWorkspacePreferences();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(true);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [tabletPreferenceSet, setTabletPreferenceSet] = useState(false);

  useEffect(() => {
    if (sidebarBehavior === "expanded") {
      setSidebarCollapsed(false);
      setTabletPreferenceSet(true);
      return;
    }
    if (sidebarBehavior === "collapsed") {
      setSidebarCollapsed(true);
      setTabletPreferenceSet(true);
      return;
    }
    if (productivity?.sidebarCollapsedPref != null) {
      setSidebarCollapsed(productivity.sidebarCollapsedPref);
      setTabletPreferenceSet(true);
    }
  }, [productivity?.sidebarCollapsedPref, sidebarBehavior]);

  useEffect(() => {
    if (sidebarBehavior !== "auto") {
      return;
    }
    if (productivity?.sidebarCollapsedPref != null) {
      return;
    }
    if (isLaptopUp) {
      setSidebarCollapsed(false);
      setTabletPreferenceSet(false);
      return;
    }
    if (isTablet && !tabletPreferenceSet) {
      setSidebarCollapsed(true);
      setTabletPreferenceSet(true);
    }
  }, [
    isLaptopUp,
    isTablet,
    productivity?.sidebarCollapsedPref,
    sidebarBehavior,
    tabletPreferenceSet,
  ]);

  useEffect(() => {
    if (!isMobile) {
      setMobileOpen(false);
    }
  }, [isMobile]);

  useEffect(() => {
    if (!isMobile || !mobileOpen) {
      return;
    }
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
    };
  }, [isMobile, mobileOpen]);

  return (
    <div className="flex min-h-screen overflow-x-hidden bg-background text-foreground">
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <Sidebar
        collapsed={sidebarCollapsed}
        mobileOpen={mobileOpen}
        onClose={() => setMobileOpen(false)}
        onToggle={() => {
          setSidebarCollapsed((current) => {
            const next = !current;
            productivity?.setSidebarCollapsedPref(next);
            return next;
          });
          setTabletPreferenceSet(true);
        }}
      />
      <div className="flex min-w-0 flex-1 flex-col">
        <OfflineBanner />
        <Topbar
          onOpenMenu={() => setMobileOpen(true)}
          trailing={<HelpMenuButton />}
        />
        <main
          className="animate-fade-in min-w-0 flex-1 overflow-x-hidden overflow-y-auto"
          id="main-content"
          tabIndex={-1}
        >
          <PageContainer className="p-3 sm:p-5 md:p-6 xl:p-8 desktop:p-8">
            {children}
          </PageContainer>
        </main>
        <footer className="hidden h-8 items-center justify-between border-t border-border px-4 text-micro text-subtle sm:flex sm:px-6">
          <span>AI_Forge / investigation workspace</span>
          <span className="hidden md:inline">
            Original evidence remains immutable
          </span>
        </footer>
      </div>
      {productivity && (
        <>
          <CommandPalette />
          <NotificationCenter />
          <OnboardingWalkthrough />
        </>
      )}
    </div>
  );
}
