import { Shield } from "lucide-react";

import { LoginForm } from "../components/auth/LoginForm";
import { appConfig } from "../config/env";

export function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-md rounded-2xl border border-border bg-background/80 p-8 shadow-panel">
        <div className="mb-8 flex flex-col items-center text-center">
          <span className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <Shield aria-hidden="true" size={22} />
          </span>
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-primary">
            {appConfig.appName}
          </p>
          <h1 className="mt-2 text-2xl font-semibold text-foreground">Sign in</h1>
          <p className="mt-2 text-sm text-muted">
            Secure access to investigation workspaces.
          </p>
        </div>
        <LoginForm />
      </div>
    </div>
  );
}
