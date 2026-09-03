import { Shield } from "lucide-react";

import { LoginForm } from "../components/auth/LoginForm";
import { appConfig } from "../config/env";

export function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
      <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-950/80 p-8 shadow-panel">
        <div className="mb-8 flex flex-col items-center text-center">
          <span className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-400/10 text-cyan-300">
            <Shield aria-hidden="true" size={22} />
          </span>
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-cyan-400">
            {appConfig.appName}
          </p>
          <h1 className="mt-2 text-2xl font-semibold text-slate-100">Sign in</h1>
          <p className="mt-2 text-sm text-slate-500">
            Secure access to investigation workspaces.
          </p>
        </div>
        <LoginForm />
      </div>
    </div>
  );
}
