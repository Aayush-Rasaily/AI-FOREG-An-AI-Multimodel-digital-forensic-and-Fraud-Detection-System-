import type { ComponentType } from "react";
import { NavLink } from "react-router-dom";
import {
  ChevronLeft,
  ChevronRight,
  FileArchive,
  FileBarChart,
  LayoutDashboard,
  Search,
  Settings,
  Shield,
  Users,
  X,
  Cpu,
  BrainCircuit,
  Activity,
  Rocket,
  ArrowLeftRight,
  UserRound,
  ChartColumn,
  HeartPulse,
} from "lucide-react";

import { useOptionalAuth } from "../../context/AuthContext";
import { cn } from "../../lib/utils";
import { SmartSidebarExtras } from "./SmartSidebarExtras";

interface SidebarProps {
  collapsed: boolean;
  mobileOpen: boolean;
  onClose: () => void;
  onToggle: () => void;
}

interface NavigationItem {
  label: string;
  to: string;
  icon: ComponentType<{ size?: number; strokeWidth?: number }>;
  permission?: string;
}

const workspaceItems: NavigationItem[] = [
  { label: "Dashboard", to: "/dashboard", icon: LayoutDashboard },
  { label: "Investigations", to: "/investigations", icon: Search },
  { label: "Evidence", to: "/evidence", icon: FileArchive },
  { label: "Reports", to: "/reports", icon: FileBarChart },
  { label: "Analytics", to: "/analytics", icon: ChartColumn },
  {
    label: "Platform Health",
    to: "/platform-health",
    icon: HeartPulse,
    permission: "platform_validation.view",
  },
];

const systemItems: NavigationItem[] = [
  { label: "AI Models", to: "/ai-models", icon: BrainCircuit },
  { label: "System", to: "/system", icon: Cpu, permission: "system.monitor" },
  {
    label: "Deployment",
    to: "/deployment",
    icon: Rocket,
    permission: "system.monitor",
  },
  {
    label: "Monitoring",
    to: "/monitoring",
    icon: Activity,
    permission: "system.monitor",
  },
  {
    label: "Users",
    to: "/users",
    icon: Users,
    permission: "admin.manage_users",
  },
  {
    label: "Security",
    to: "/security",
    icon: Shield,
    permission: "security.view",
  },
  {
    label: "Exchange",
    to: "/interoperability",
    icon: ArrowLeftRight,
    permission: "interop.export",
  },
  { label: "Profile", to: "/profile", icon: UserRound },
  { label: "Settings", to: "/settings", icon: Settings },
];

function NavigationGroup({
  items,
  collapsed,
  onNavigate,
}: {
  items: NavigationItem[];
  collapsed: boolean;
  onNavigate: () => void;
}) {
  return (
    <nav className="space-y-1">
      {items.map(({ icon: Icon, label, to }) => (
        <NavLink
          className={({ isActive }) =>
            cn(
              "group flex min-h-11 items-center gap-3 rounded-lg px-3 py-2.5 text-sm duration-fast transition-colors",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              isActive
                ? "bg-primary-soft text-primary"
                : "text-muted hover:bg-surface-muted hover:text-foreground",
              collapsed && "justify-center px-2",
            )
          }
          key={to}
          onClick={onNavigate}
          title={collapsed ? label : undefined}
          to={to}
        >
          <Icon aria-hidden="true" size={17} strokeWidth={1.8} />
          {!collapsed && <span>{label}</span>}
        </NavLink>
      ))}
    </nav>
  );
}

export function Sidebar({
  collapsed,
  mobileOpen,
  onClose,
  onToggle,
}: SidebarProps) {
  const auth = useOptionalAuth();
  const visibleSystemItems = systemItems.filter((item) => {
    if (!item.permission) {
      return true;
    }
    if (!auth) {
      return true;
    }
    if (!auth.user) {
      return false;
    }
    return auth.hasPermission(item.permission);
  });

  return (
    <>
      {mobileOpen && (
        <button
          aria-label="Close navigation"
          className={cn(
            "fixed inset-0 z-30 bg-background/80 backdrop-blur-[2px] sm:hidden",
            "animate-fade-in",
          )}
          onClick={onClose}
          type="button"
        />
      )}
      <aside
        aria-label="Primary navigation"
        className={cn(
          // Mobile: off-canvas drawer. Tablet+: in-flow collapsible rail.
          "fixed inset-y-0 left-0 z-40 flex w-[min(18rem,88vw)] flex-col border-r border-border bg-background-offset",
          "duration-normal transition-[transform,width] ease-[var(--ds-ease-default)]",
          "sm:relative sm:z-0 sm:w-64 sm:translate-x-0",
          collapsed ? "sm:w-[76px]" : "sm:w-64",
          mobileOpen ? "translate-x-0" : "-translate-x-full sm:translate-x-0",
        )}
      >
        <div className="flex h-16 items-center justify-between border-b border-border px-4">
          <NavLink
            aria-label="AI-FORGE dashboard"
            className={cn(
              "flex items-center gap-3 rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              collapsed && "sm:mx-auto",
            )}
            onClick={onClose}
            to="/dashboard"
          >
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-soft text-primary">
              <Shield aria-hidden="true" size={18} strokeWidth={1.8} />
            </span>
            {!collapsed && (
              <span className="text-body font-semibold tracking-[0.18em] text-foreground">
                AI-FORGE
              </span>
            )}
          </NavLink>
          <button
            aria-label="Close navigation"
            className={cn(
              "rounded-md p-2 text-muted hover:bg-surface-muted hover:text-foreground sm:hidden",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
            )}
            onClick={onClose}
            type="button"
          >
            <X aria-hidden="true" size={18} />
          </button>
        </div>

        <div className="flex-1 space-y-7 overflow-y-auto px-3 py-6">
          <SmartSidebarExtras collapsed={collapsed} onNavigate={onClose} />
          <div>
            {!collapsed && (
              <p className="mb-3 px-3 text-micro font-semibold uppercase tracking-[0.18em] text-subtle">
                Workspace
              </p>
            )}
            <NavigationGroup
              collapsed={collapsed}
              items={workspaceItems}
              onNavigate={onClose}
            />
          </div>
          <div>
            {!collapsed && (
              <p className="mb-3 px-3 text-micro font-semibold uppercase tracking-[0.18em] text-subtle">
                System
              </p>
            )}
            <NavigationGroup
              collapsed={collapsed}
              items={visibleSystemItems}
              onNavigate={onClose}
            />
          </div>
        </div>

        <div className="border-t border-border p-3">
          <button
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            className={cn(
              "hidden w-full min-h-11 items-center justify-center gap-2 rounded-lg p-2 text-caption text-subtle",
              "hover:bg-surface-muted hover:text-foreground sm:flex",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              "duration-fast transition-colors",
            )}
            onClick={onToggle}
            type="button"
          >
            {collapsed ? (
              <ChevronRight aria-hidden="true" size={16} />
            ) : (
              <>
                <ChevronLeft aria-hidden="true" size={16} />
                Collapse sidebar
              </>
            )}
          </button>
        </div>
      </aside>
    </>
  );
}
