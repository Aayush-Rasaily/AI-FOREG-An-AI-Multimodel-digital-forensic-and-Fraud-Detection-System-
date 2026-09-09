import { WifiOff } from "lucide-react";

import { ErrorState } from "./ErrorState";

export function NetworkErrorState({ onRetry }: { onRetry?: () => void }) {
  return (
    <ErrorState
      description="The API is unavailable or the browser is offline. Check connectivity and retry."
      onRetry={onRetry}
      title="Cannot reach AI-FORGE services"
    />
  );
}

export function NetworkErrorIcon() {
  return <WifiOff aria-hidden="true" size={20} />;
}

