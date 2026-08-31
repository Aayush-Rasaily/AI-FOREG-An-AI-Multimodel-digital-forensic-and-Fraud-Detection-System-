import { useState, type ReactNode } from "react";

import { Sidebar } from "../components/navigation/Sidebar";
import { Topbar } from "../components/navigation/Topbar";

export function AppShell({ children }: { children: ReactNode }) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100">
      <Sidebar
        collapsed={sidebarCollapsed}
        mobileOpen={mobileOpen}
        onClose={() => setMobileOpen(false)}
        onToggle={() => setSidebarCollapsed((current) => !current)}
      />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar onOpenMenu={() => setMobileOpen(true)} />
        <main className="min-w-0 flex-1 overflow-y-auto">
          <div className="mx-auto w-full max-w-[1800px] p-4 sm:p-6 xl:p-8">{children}</div>
        </main>
        <footer className="hidden h-8 items-center justify-between border-t border-slate-800 px-6 text-[10px] text-slate-600 sm:flex">
          <span>AI-FORGE / investigation workspace</span>
          <span>Evidence handling controls pending integration</span>
        </footer>
      </div>
    </div>
  );
}

