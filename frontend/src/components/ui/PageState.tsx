import { FileSearch, ShieldOff, WifiOff } from "lucide-react";
import type { ReactNode } from "react";

import { EmptyState } from "./EmptyState";
import { ErrorState } from "./ErrorState";
import { LoadingSkeleton } from "./Skeleton";
import { LoadingState } from "./LoadingState";

type PageStateKind =
  | "loading"
  | "empty"
  | "error"
  | "permission"
  | "offline";

interface PageStateProps {
  kind: PageStateKind;
  title?: string;
  description?: string;
  onRetry?: () => void;
  action?: ReactNode;
}

const defaults: Record<PageStateKind, { title: string; description: string }> = {
  loading: {
    title: "Loading workspace",
    description: "Retrieving investigation data.",
  },
  empty: {
    title: "No records",
    description: "Nothing is available in this view yet.",
  },
  error: {
    title: "Workspace unavailable",
    description: "The requested information could not be loaded.",
  },
  permission: {
    title: "Permission denied",
    description: "Your account cannot access this area.",
  },
  offline: {
    title: "You appear to be offline",
    description: "Reconnect to the network and try again.",
  },
};

export function PageState({
  kind,
  title,
  description,
  onRetry,
  action,
}: PageStateProps) {
  const copy = defaults[kind];
  if (kind === "loading") {
    return (
      <div>
        <LoadingState label={title ?? copy.title} />
        <LoadingSkeleton rows={3} />
      </div>
    );
  }
  if (kind === "error") {
    return (
      <ErrorState
        description={description ?? copy.description}
        onRetry={onRetry}
        title={title ?? copy.title}
      />
    );
  }
  const icon =
    kind === "permission" ? (
      <ShieldOff aria-hidden="true" size={20} />
    ) : kind === "offline" ? (
      <WifiOff aria-hidden="true" size={20} />
    ) : (
      <FileSearch aria-hidden="true" size={20} />
    );
  return (
    <EmptyState
      action={action}
      description={description ?? copy.description}
      icon={icon}
      title={title ?? copy.title}
    />
  );
}

export function PermissionDeniedState({ onRetry }: { onRetry?: () => void }) {
  return <PageState kind="permission" onRetry={onRetry} />;
}

export function OfflineState({ onRetry }: { onRetry?: () => void }) {
  return (
    <PageState
      action={
        onRetry ? (
          <button
            className="text-caption rounded-md border border-border px-3 py-2"
            onClick={onRetry}
            type="button"
          >
            Retry
          </button>
        ) : undefined
      }
      kind="offline"
    />
  );
}
