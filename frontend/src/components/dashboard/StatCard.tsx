import type { ComponentType } from "react";

import { ArrowUpRight } from "lucide-react";

import { Card } from "../ui/Card";

interface StatCardProps {
  label: string;
  value: string;
  detail: string;
  icon: ComponentType<{ size?: number; strokeWidth?: number }>;
}

export function StatCard({ label, value, detail, icon: Icon }: StatCardProps) {
  return (
    <Card className="p-5">
      <div className="flex items-start justify-between">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-800 bg-slate-950 text-cyan-300">
          <Icon aria-hidden="true" size={17} strokeWidth={1.7} />
        </div>
        <ArrowUpRight aria-hidden="true" className="text-slate-700" size={16} />
      </div>
      <p className="mt-5 text-xs text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold tracking-tight text-slate-100">{value}</p>
      <p className="mt-1 text-[11px] text-slate-600">{detail}</p>
    </Card>
  );
}

