import { Server, ShieldCheck } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";
import { StatusIndicator } from "../ui/StatusIndicator";

export function SystemStatusCard() {
  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>System status</CardTitle>
          <p className="mt-1 text-xs text-slate-500">Operational signals from connected services</p>
        </div>
        <ShieldCheck aria-hidden="true" className="text-slate-600" size={17} />
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-3">
          <div className="flex items-center gap-3">
            <Server aria-hidden="true" className="text-slate-500" size={16} />
            <span className="text-xs text-slate-300">Application API</span>
          </div>
          <StatusIndicator label="Awaiting signal" tone="pending" />
        </div>
        <div className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-3">
          <div className="flex items-center gap-3">
            <span className="h-2 w-2 rounded-full bg-slate-600" />
            <span className="text-xs text-slate-300">Analysis workers</span>
          </div>
          <StatusIndicator label="Not connected" tone="offline" />
        </div>
      </CardContent>
    </Card>
  );
}

