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
  X,
  Cpu,
} from "lucide-react";

import { cn } from "../../lib/utils";

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
}

const workspaceItems: NavigationItem[] = [
  { label: "Dashboard", to: "/dashboard", icon: LayoutDashboard },
  { label: "Investigations", to: "/investigations", icon: Search },
  { label: "Evidence", to: "/evidence", icon: FileArchive },
  { label: "Reports", to: "/reports", icon: FileBarChart },
];

const systemItems: NavigationItem[] = [
  { label: "System", to: "/system", icon: Cpu },
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
              "group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400/80",
              isActive
                ? "bg-cyan-400/10 text-cyan-200"
                : "text-slate-500 hover:bg-slate-800/80 hover:text-slate-200",
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
  return (
    <>
      {mobileOpen && (
        <button
          aria-label="Close navigation"
          className="fixed inset-0 z-30 bg-slate-950/70 lg:hidden"
          onClick={onClose}
          type="button"
        />
      )}
      <aside
        aria-label="Primary navigation"
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-slate-800 bg-slate-950 transition-transform duration-200 lg:relative lg:z-0 lg:translate-x-0",
          collapsed ? "lg:w-[76px]" : "lg:w-64",
          mobileOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex h-16 items-center justify-between border-b border-slate-800 px-4">
          <NavLink
            aria-label="AI-FORGE dashboard"
            className={cn("flex items-center gap-3", collapsed && "lg:mx-auto")}
            onClick={onClose}
            to="/dashboard"
          >
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-cyan-400/10 text-cyan-300">
              <Shield aria-hidden="true" size={18} strokeWidth={1.8} />
            </span>
            {!collapsed && (
              <span className="text-sm font-semibold tracking-[0.18em] text-slate-100">
                AI-FORGE
              </span>
            )}
          </NavLink>
          <button
            aria-label="Close navigation"
            className="rounded-md p-1.5 text-slate-500 hover:bg-slate-800 hover:text-slate-100 lg:hidden"
            onClick={onClose}
            type="button"
          >
            <X aria-hidden="true" size={18} />
          </button>
        </div>

        <div className="flex-1 space-y-7 overflow-y-auto px-3 py-6">
          <div>
            {!collapsed && (
              <p className="mb-3 px-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-600">
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
              <p className="mb-3 px-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-600">
                System
              </p>
            )}
            <NavigationGroup
              collapsed={collapsed}
              items={systemItems}
              onNavigate={onClose}
            />
          </div>
        </div>

        <div className="border-t border-slate-800 p-3">
          <button
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            className="hidden w-full items-center justify-center gap-2 rounded-lg p-2 text-xs text-slate-600 hover:bg-slate-800 hover:text-slate-300 lg:flex"
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

