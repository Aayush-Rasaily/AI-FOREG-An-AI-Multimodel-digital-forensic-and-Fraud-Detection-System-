import { WifiOff } from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "./Button";

/** Live offline / reconnect banner for the application shell. */
export function OfflineBanner() {
  const [offline, setOffline] = useState(
    typeof navigator !== "undefined" ? !navigator.onLine : false,
  );

  useEffect(() => {
    const goOffline = () => setOffline(true);
    const goOnline = () => setOffline(false);
    window.addEventListener("offline", goOffline);
    window.addEventListener("online", goOnline);
    return () => {
      window.removeEventListener("offline", goOffline);
      window.removeEventListener("online", goOnline);
    };
  }, []);

  if (!offline) {
    return null;
  }

  return (
    <div
      aria-live="assertive"
      className="animate-slide-in-down flex items-center justify-between gap-3 border-b border-warning/40 bg-warning-soft px-4 py-2 text-caption text-warning"
      role="status"
    >
      <span className="inline-flex items-center gap-2">
        <WifiOff aria-hidden="true" size={14} />
        You are offline. Changes may not sync until connectivity returns.
      </span>
      <Button
        onClick={() => window.location.reload()}
        size="sm"
        type="button"
        variant="secondary"
      >
        Retry
      </Button>
    </div>
  );
}
