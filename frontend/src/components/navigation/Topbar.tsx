import { Menu, Bell, Command, CircleHelp } from "lucide-react";
import { Link, useLocation } from "react-router-dom";

import { UserAvatar } from "../auth/UserAvatar";
import { appConfig } from "../../config/env";
import { useOptionalAuth } from "../../context/AuthContext";
import { StatusIndicator } from "../ui/StatusIndicator";
import { Tooltip } from "../ui/Tooltip";

interface TopbarProps {
  onOpenMenu: () => void;
}

const pageTitles: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/investigations": "Investigations",
  "/evidence": "Evidence",
  "/reports": "Reports",
  "/settings": "Settings",
  "/system": "System",
  "/deployment": "Deployment",
  "/monitoring": "Monitoring",
  "/profile": "Profile",
  "/users": "Users",
  "/security": "Security",
};

export function Topbar({ onOpenMenu }: TopbarProps) {
  const location = useLocation();
  const auth = useOptionalAuth();
  const title = pageTitles[location.pathname] || "Investigation workspace";

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-slate-800 bg-slate-950/80 px-4 backdrop-blur-sm sm:px-6">
      <div className="flex min-w-0 items-center gap-3">
        <button
          aria-label="Open navigation"
          className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-slate-100 lg:hidden"
          onClick={onOpenMenu}
          type="button"
        >
          <Menu aria-hidden="true" size={19} />
        </button>
        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-slate-100">{title}</p>
          <p className="hidden truncate text-[11px] text-slate-600 sm:block">
            {appConfig.appName} / secure workspace
          </p>
        </div>
      </div>
      <div className="flex items-center gap-1 sm:gap-3">
        <StatusIndicator
          className="hidden sm:inline-flex"
          label="API status pending"
          tone="pending"
        />
        <Tooltip label="Command palette">
          <button
            aria-label="Open command palette"
            className="rounded-lg p-2 text-slate-500 hover:bg-slate-800 hover:text-slate-200"
            type="button"
          >
            <Command aria-hidden="true" size={17} />
          </button>
        </Tooltip>
        <Tooltip label="Help">
          <button
            aria-label="Open help"
            className="rounded-lg p-2 text-slate-500 hover:bg-slate-800 hover:text-slate-200"
            type="button"
          >
            <CircleHelp aria-hidden="true" size={17} />
          </button>
        </Tooltip>
        <Tooltip label="Notifications">
          <button
            aria-label="Open notifications"
            className="relative rounded-lg p-2 text-slate-500 hover:bg-slate-800 hover:text-slate-200"
            type="button"
          >
            <Bell aria-hidden="true" size={17} />
          </button>
        </Tooltip>
        {auth?.user ? (
          <Link
            aria-label="Open profile"
            className="ml-1 hidden sm:block"
            to="/profile"
          >
            <UserAvatar name={auth.user.display_name} />
          </Link>
        ) : (
          <div className="ml-1 hidden h-7 w-7 items-center justify-center rounded-full border border-slate-700 bg-slate-800 text-[10px] font-semibold text-slate-300 sm:flex">
            IN
          </div>
        )}
      </div>
    </header>
  );
}
