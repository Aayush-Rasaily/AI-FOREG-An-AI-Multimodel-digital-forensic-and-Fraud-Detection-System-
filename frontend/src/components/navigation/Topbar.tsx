import { Menu, Bell, Command, CircleHelp } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import type { ReactNode } from "react";

import { UserAvatar } from "../auth/UserAvatar";
import { ThemeToggle } from "../theme/ThemeToggle";
import { appConfig } from "../../config/env";
import { useOptionalAuth } from "../../context/AuthContext";
import { useOptionalProductivity } from "../../context/ProductivityContext";
import { cn } from "../../lib/utils";
import { StatusIndicator } from "../ui/StatusIndicator";
import { Tooltip } from "../ui/Tooltip";

interface TopbarProps {
  onOpenMenu: () => void;
  trailing?: ReactNode;
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
  "/interoperability": "Exchange",
};

const iconButtonClass = cn(
  "inline-flex min-h-11 min-w-11 items-center justify-center rounded-lg p-2 text-muted",
  "hover:bg-surface-muted hover:text-foreground duration-fast transition-colors",
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
);

export function Topbar({ onOpenMenu, trailing }: TopbarProps) {
  const location = useLocation();
  const auth = useOptionalAuth();
  const productivity = useOptionalProductivity();
  const title = pageTitles[location.pathname] || "Investigation workspace";
  const unread = productivity?.unreadCount ?? 0;

  return (
    <header
      className="flex h-16 shrink-0 items-center justify-between border-b border-border bg-surface/80 px-3 backdrop-blur-sm sm:px-6"
      role="banner"
    >
      <div className="flex min-w-0 items-center gap-2 sm:gap-3">
        <button
          aria-label="Open navigation"
          className={cn(iconButtonClass, "sm:hidden")}
          onClick={onOpenMenu}
          type="button"
        >
          <Menu aria-hidden="true" size={19} />
        </button>
        <div className="min-w-0">
          <p className="truncate text-body font-medium text-foreground">{title}</p>
          <p className="hidden truncate text-caption text-subtle sm:block">
            {appConfig.appName} / secure workspace
          </p>
        </div>
      </div>
      <div className="flex items-center gap-0.5 sm:gap-2">
        <StatusIndicator
          className="mr-1 hidden md:inline-flex"
          label="API status pending"
          tone="pending"
        />
        {trailing}
        <ThemeToggle compact />
        <Tooltip label="Command palette (Ctrl+K)">
          <button
            aria-label="Open command palette"
            className={cn(iconButtonClass, "hidden sm:inline-flex")}
            onClick={() => productivity?.openCommandPalette("commands")}
            type="button"
          >
            <Command aria-hidden="true" size={17} />
          </button>
        </Tooltip>
        <Tooltip label="Keyboard shortcuts help">
          <button
            aria-label="Open help"
            className={iconButtonClass}
            onClick={() => productivity?.openCommandPalette("help")}
            type="button"
          >
            <CircleHelp aria-hidden="true" size={17} />
          </button>
        </Tooltip>
        <Tooltip label="Notifications">
          <button
            aria-label="Open notifications"
            className={cn(iconButtonClass, "relative")}
            onClick={() => productivity?.setNotificationOpen(true)}
            type="button"
          >
            <Bell aria-hidden="true" size={17} />
            {unread > 0 && (
              <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-danger" />
            )}
          </button>
        </Tooltip>
        {auth?.user ? (
          <Link
            aria-label="Open profile"
            className="ml-1 hidden rounded-pill focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring sm:block"
            to="/profile"
          >
            <UserAvatar name={auth.user.display_name} />
          </Link>
        ) : (
          <div className="ml-1 hidden h-7 w-7 items-center justify-center rounded-pill border border-border bg-surface-muted text-caption font-semibold text-muted sm:flex">
            IN
          </div>
        )}
      </div>
    </header>
  );
}
