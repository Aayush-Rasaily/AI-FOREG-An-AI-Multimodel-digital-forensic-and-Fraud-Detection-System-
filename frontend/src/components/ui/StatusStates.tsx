import { AlertTriangle, Clock3, ServerCrash, ShieldOff, WifiOff } from "lucide-react";

import { Button } from "./Button";
import { EmptyState } from "./EmptyState";
import { ErrorState } from "./ErrorState";
import { NetworkErrorState } from "./NetworkErrorState";

export { NetworkErrorState };

export function OfflineState({ onRetry }: { onRetry?: () => void }) {
  return (
    <EmptyState
      action={
        onRetry ? (
          <Button onClick={onRetry} size="sm" type="button" variant="secondary">
            Retry connection
          </Button>
        ) : undefined
      }
      description="This workspace needs a network connection to load investigation data."
      icon={<WifiOff aria-hidden="true" size={20} />}
      title="You are offline"
    />
  );
}

export function ForbiddenState({ onBack }: { onBack?: () => void }) {
  return (
    <EmptyState
      action={
        onBack ? (
          <Button onClick={onBack} size="sm" type="button" variant="secondary">
            Go back
          </Button>
        ) : undefined
      }
      description="Your role does not include permission for this investigation area."
      icon={<ShieldOff aria-hidden="true" size={20} />}
      title="Access forbidden"
    />
  );
}

export function ServerErrorState({ onRetry }: { onRetry?: () => void }) {
  return (
    <ErrorState
      description="The server returned an unexpected error. Retry, or contact an administrator if it persists."
      onRetry={onRetry}
      title="Something went wrong (500)"
    />
  );
}

export function TimeoutState({ onRetry }: { onRetry?: () => void }) {
  return (
    <EmptyState
      action={
        onRetry ? (
          <Button onClick={onRetry} size="sm" type="button" variant="secondary">
            Try again
          </Button>
        ) : undefined
      }
      description="The request took too long. Check network conditions and retry."
      icon={<Clock3 aria-hidden="true" size={20} />}
      title="Request timed out"
    />
  );
}

export function PermissionDeniedState({ onRetry }: { onRetry?: () => void }) {
  return (
    <EmptyState
      action={
        onRetry ? (
          <Button onClick={onRetry} size="sm" type="button" variant="secondary">
            Refresh session
          </Button>
        ) : undefined
      }
      description="Sign in again or ask an administrator to grant the required permission."
      icon={<AlertTriangle aria-hidden="true" size={20} />}
      title="Permission denied"
    />
  );
}

export function ServiceUnavailableState({ onRetry }: { onRetry?: () => void }) {
  return (
    <ErrorState
      description="A required service is temporarily unavailable."
      onRetry={onRetry}
      title="Service unavailable"
    />
  );
}

export function ServerCrashIcon() {
  return <ServerCrash aria-hidden="true" size={20} />;
}
