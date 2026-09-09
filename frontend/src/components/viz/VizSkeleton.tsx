import { Card, CardContent } from "../ui/Card";

export function VizSkeleton({ label = "Loading visualization" }: { label?: string }) {
  return (
    <Card aria-busy="true" aria-label={label} className="min-w-0">
      <CardContent className="space-y-3 py-5">
        <div className="h-4 w-1/3 animate-pulse rounded bg-surface-muted" />
        <div className="h-3 w-1/2 animate-pulse rounded bg-surface-muted" />
        <div className="flex h-28 items-end gap-2 pt-2">
          {[40, 70, 55, 90, 35, 65].map((h, i) => (
            <div
              className="flex-1 animate-pulse rounded-t bg-surface-muted"
              key={i}
              style={{ height: `${h}%`, animationDelay: `${i * 80}ms` }}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
