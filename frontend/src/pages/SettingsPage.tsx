import { useState } from "react";
import { Link } from "react-router-dom";
import {
  Bell,
  Keyboard,
  LayoutDashboard,
  LockKeyhole,
  PanelLeft,
  SlidersHorizontal,
  Sparkles,
} from "lucide-react";

import { ContextualHelp } from "../components/help/HelpChrome";
import { OnboardingWalkthrough } from "../components/help/OnboardingWalkthrough";
import { PageHeader } from "../components/layout/PageHeader";
import { ThemeToggle } from "../components/theme/ThemeToggle";
import { Button } from "../components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { FormField } from "../components/ui/FormField";
import { Select } from "../components/ui/Select";
import { useProductivity } from "../context/ProductivityContext";
import type {
  DefaultDashboardPath,
  PreferredView,
  SidebarBehavior,
} from "../hooks/useInvestigatorPreferences";
import { useWorkspacePreferences } from "../hooks/useWorkspacePreferences";
import { useTheme } from "../theme/ThemeProvider";

export function SettingsPage() {
  const { density, setDensity, preference, setPreference } = useTheme();
  const { preferredView, setPreferredView } = useProductivity();
  const {
    defaultDashboard,
    setDefaultDashboard,
    notifyJobs,
    setNotifyJobs,
    notifySystem,
    setNotifySystem,
    setOnboardingDismissed,
    sidebarBehavior,
    setSidebarBehavior,
  } = useWorkspacePreferences();
  const [replayOnboarding, setReplayOnboarding] = useState(false);

  return (
    <div className="space-y-4">
      <PageHeader
        description="Workspace preferences persist locally in this browser. They do not change server policies."
        eyebrow="Configuration"
        title="Settings"
      />

      <ContextualHelp
        body="Use density and theme for readability during long investigations. Sidebar and default dashboard control first-paint navigation. Notification toggles only affect local toast/center behavior."
        title="About workspace preferences"
      />

      <div className="grid max-w-5xl gap-4 xl:grid-cols-2">
        <Card className="duration-fast transition-shadow hover:shadow-md">
          <CardHeader>
            <CardTitle>Appearance</CardTitle>
            <SlidersHorizontal aria-hidden="true" className="text-subtle" size={17} />
          </CardHeader>
          <CardContent className="space-y-5">
            <FormField htmlFor="density" label="Interface density">
              <Select
                aria-label="Interface density"
                className="w-full"
                id="density"
                onChange={(event) =>
                  setDensity(
                    event.target.value === "compact" ? "compact" : "comfortable",
                  )
                }
                value={density}
              >
                <option value="comfortable">Comfortable</option>
                <option value="compact">Compact</option>
              </Select>
            </FormField>
            <FormField htmlFor="theme-pref" label="Theme">
              <Select
                aria-label="Theme preference"
                className="w-full"
                id="theme-pref"
                onChange={(event) =>
                  setPreference(
                    event.target.value as "light" | "dark" | "system",
                  )
                }
                value={preference}
              >
                <option value="system">System</option>
                <option value="light">Light</option>
                <option value="dark">Dark</option>
              </Select>
            </FormField>
            <div className="flex items-center justify-between border-t border-border pt-4">
              <div>
                <p className="text-caption text-foreground">Quick theme toggle</p>
                <p className="mt-1 text-caption text-subtle">
                  Same control as the top bar
                </p>
              </div>
              <ThemeToggle />
            </div>
          </CardContent>
        </Card>

        <Card className="duration-fast transition-shadow hover:shadow-md">
          <CardHeader>
            <CardTitle>Navigation & workspace</CardTitle>
            <PanelLeft aria-hidden="true" className="text-subtle" size={17} />
          </CardHeader>
          <CardContent className="space-y-5">
            <FormField htmlFor="sidebar-behavior" label="Sidebar behavior">
              <Select
                aria-label="Sidebar behavior"
                className="w-full"
                id="sidebar-behavior"
                onChange={(event) =>
                  setSidebarBehavior(event.target.value as SidebarBehavior)
                }
                value={sidebarBehavior}
              >
                <option value="auto">Auto (responsive)</option>
                <option value="expanded">Prefer expanded</option>
                <option value="collapsed">Prefer collapsed</option>
              </Select>
            </FormField>
            <FormField htmlFor="default-dashboard" label="Default dashboard">
              <Select
                aria-label="Default dashboard"
                className="w-full"
                id="default-dashboard"
                onChange={(event) =>
                  setDefaultDashboard(
                    event.target.value as DefaultDashboardPath,
                  )
                }
                value={defaultDashboard}
              >
                <option value="/dashboard">Executive dashboard</option>
                <option value="/investigations">Investigations</option>
                <option value="/analytics">Analytics</option>
                <option value="/evidence">Evidence</option>
              </Select>
            </FormField>
            <FormField htmlFor="preferred-view" label="Default investigation view">
              <Select
                aria-label="Default investigation view"
                className="w-full"
                id="preferred-view"
                onChange={(event) =>
                  setPreferredView(event.target.value as PreferredView)
                }
                value={preferredView}
              >
                <option value="overview">Overview</option>
                <option value="evidence">Evidence</option>
                <option value="timeline">Timeline</option>
                <option value="forensics">Forensics</option>
              </Select>
            </FormField>
          </CardContent>
        </Card>

        <Card className="duration-fast transition-shadow hover:shadow-md">
          <CardHeader>
            <CardTitle>Notifications</CardTitle>
            <Bell aria-hidden="true" className="text-subtle" size={17} />
          </CardHeader>
          <CardContent className="space-y-4">
            <label className="flex items-center justify-between gap-3 text-caption text-foreground">
              Job / processing alerts
              <input
                aria-label="Toggle job notifications"
                checked={notifyJobs}
                className="h-4 w-4 accent-[var(--color-primary)]"
                onChange={(event) => setNotifyJobs(event.target.checked)}
                type="checkbox"
              />
            </label>
            <label className="flex items-center justify-between gap-3 text-caption text-foreground">
              System alerts
              <input
                aria-label="Toggle system notifications"
                checked={notifySystem}
                className="h-4 w-4 accent-[var(--color-primary)]"
                onChange={(event) => setNotifySystem(event.target.checked)}
                type="checkbox"
              />
            </label>
            <p className="text-caption text-subtle">
              Preferences apply to the local notification center and toast mirror.
            </p>
          </CardContent>
        </Card>

        <Card className="duration-fast transition-shadow hover:shadow-md">
          <CardHeader>
            <CardTitle>Help & onboarding</CardTitle>
            <Keyboard aria-hidden="true" className="text-subtle" size={17} />
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-caption text-muted">
              Replay the optional first-run walkthrough or open the shortcuts
              reference from the top bar.
            </p>
            <Button
              onClick={() => {
                setOnboardingDismissed(false);
                setReplayOnboarding(true);
              }}
              size="sm"
              type="button"
              variant="secondary"
            >
              <Sparkles aria-hidden="true" size={14} />
              Replay welcome tour
            </Button>
            <Link className="block" to="/dashboard">
              <Button size="sm" type="button" variant="ghost">
                <LayoutDashboard aria-hidden="true" size={14} />
                Open dashboard
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card className="duration-fast transition-shadow hover:shadow-md xl:col-span-2">
          <CardHeader>
            <CardTitle>Access and integrations</CardTitle>
            <LockKeyhole aria-hidden="true" className="text-subtle" size={17} />
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-3">
            <Link to="/security">
              <Button className="w-full" type="button" variant="secondary">
                Security governance
              </Button>
            </Link>
            <Link to="/deployment">
              <Button className="w-full" type="button" variant="secondary">
                Deployment status
              </Button>
            </Link>
            <Link to="/interoperability">
              <Button className="w-full" type="button" variant="secondary">
                Interoperability
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>

      {replayOnboarding && (
        <OnboardingWalkthrough
          forceOpen
          onCloseForced={() => setReplayOnboarding(false)}
        />
      )}
    </div>
  );
}
