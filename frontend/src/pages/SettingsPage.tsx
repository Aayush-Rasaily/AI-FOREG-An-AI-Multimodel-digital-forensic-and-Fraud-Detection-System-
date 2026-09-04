import { Link } from "react-router-dom";
import { LockKeyhole, SlidersHorizontal } from "lucide-react";

import { PageHeader } from "../components/layout/PageHeader";
import { Badge } from "../components/ui/Badge";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { Select } from "../components/ui/Select";

export function SettingsPage() {
  return (
    <div>
      <PageHeader
        description="Workspace preferences and controlled integration settings."
        eyebrow="Configuration"
        title="Settings"
      />
      <div className="grid max-w-4xl gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Workspace preferences</CardTitle>
            <SlidersHorizontal aria-hidden="true" className="text-slate-600" size={17} />
          </CardHeader>
          <CardContent className="space-y-5">
            <label className="block">
              <span className="mb-2 block text-xs text-slate-400">Interface density</span>
              <Select className="w-full" defaultValue="comfortable">
                <option value="comfortable">Comfortable</option>
                <option value="compact">Compact</option>
              </Select>
            </label>
            <div className="flex items-center justify-between border-t border-slate-800 pt-4">
              <div>
                <p className="text-xs text-slate-300">Theme</p>
                <p className="mt-1 text-[11px] text-slate-600">Dark investigation workspace</p>
              </div>
              <Badge tone="cyan">Dark first</Badge>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Access and integrations</CardTitle>
            <LockKeyhole aria-hidden="true" className="text-slate-600" size={17} />
          </CardHeader>
          <CardContent>
            <p className="text-sm leading-relaxed text-slate-500">
              Enterprise RBAC, governance policies, and compliance controls are
              managed in Security & Governance.
            </p>
            <Link
              className="mt-4 inline-flex h-8 items-center rounded-lg border border-slate-700 bg-slate-900 px-3 text-xs font-medium text-slate-100 hover:bg-slate-800"
              to="/security"
            >
              Open security governance
            </Link>
            <Link
              className="mt-3 inline-flex h-8 items-center rounded-lg border border-slate-700 bg-slate-900 px-3 text-xs font-medium text-slate-100 hover:bg-slate-800"
              to="/deployment"
            >
              Open deployment status
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
