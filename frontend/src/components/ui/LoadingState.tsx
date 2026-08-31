import { LoaderCircle } from "lucide-react";

export function LoadingState({ label = "Loading workspace" }: { label?: string }) {
  return (
    <div className="flex min-h-48 flex-col items-center justify-center gap-3 text-slate-500">
      <LoaderCircle aria-hidden="true" className="animate-spin text-cyan-400" size={22} />
      <span className="text-xs">{label}</span>
    </div>
  );
}

