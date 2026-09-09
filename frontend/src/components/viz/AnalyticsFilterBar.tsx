import type { AnalyticsFilterState } from "./types";
import { Input } from "../ui/Input";
import { Select } from "../ui/Select";
import { Button } from "../ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";

interface AnalyticsFilterBarProps {
  filters: AnalyticsFilterState;
  onChange: (next: AnalyticsFilterState) => void;
  caseOptions: Array<{ id: string; label: string }>;
  evidenceTypes: string[];
  correlationTypes: string[];
  modalities: string[];
}

export function AnalyticsFilterBar({
  filters,
  onChange,
  caseOptions,
  evidenceTypes,
  correlationTypes,
  modalities,
}: AnalyticsFilterBarProps) {
  const set = <K extends keyof AnalyticsFilterState>(
    key: K,
    value: AnalyticsFilterState[K],
  ) => onChange({ ...filters, [key]: value });

  return (
    <Card className="min-w-0">
      <CardHeader className="flex-col items-start gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <CardTitle>Interactive filters</CardTitle>
          <p className="mt-1 text-caption text-muted">
            Filters update charts and widgets live (client-side)
          </p>
        </div>
        <Button
          onClick={() =>
            onChange({
              dateFrom: "",
              dateTo: "",
              evidenceType: "all",
              risk: "all",
              confidenceMin: 0,
              status: "all",
              caseId: "all",
              aiModality: "all",
              correlationType: "all",
              selectedSliceId: null,
            })
          }
          size="sm"
          type="button"
          variant="ghost"
        >
          Reset
        </Button>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          <label className="space-y-1 text-caption text-muted">
            Date from
            <Input
              aria-label="Date from"
              onChange={(e) => set("dateFrom", e.target.value)}
              type="date"
              value={filters.dateFrom}
            />
          </label>
          <label className="space-y-1 text-caption text-muted">
            Date to
            <Input
              aria-label="Date to"
              onChange={(e) => set("dateTo", e.target.value)}
              type="date"
              value={filters.dateTo}
            />
          </label>
          <label className="space-y-1 text-caption text-muted">
            Evidence type
            <Select
              aria-label="Evidence type"
              onChange={(e) => set("evidenceType", e.target.value)}
              value={filters.evidenceType}
            >
              <option value="all">All</option>
              {evidenceTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </Select>
          </label>
          <label className="space-y-1 text-caption text-muted">
            Risk
            <Select
              aria-label="Risk"
              onChange={(e) => set("risk", e.target.value)}
              value={filters.risk}
            >
              <option value="all">All</option>
              <option value="LOW">Low</option>
              <option value="MEDIUM">Medium</option>
              <option value="HIGH">High</option>
              <option value="CRITICAL">Critical</option>
            </Select>
          </label>
          <label className="space-y-1 text-caption text-muted">
            Min confidence ({Math.round(filters.confidenceMin * 100)}%)
            <Input
              aria-label="Minimum confidence"
              max={1}
              min={0}
              onChange={(e) => set("confidenceMin", Number(e.target.value))}
              step={0.05}
              type="range"
              value={filters.confidenceMin}
            />
          </label>
          <label className="space-y-1 text-caption text-muted">
            Status
            <Select
              aria-label="Status"
              onChange={(e) => set("status", e.target.value)}
              value={filters.status}
            >
              <option value="all">All</option>
              <option value="OPEN">Open</option>
              <option value="IN_PROGRESS">In progress</option>
              <option value="ON_HOLD">On hold</option>
              <option value="COMPLETED">Completed</option>
              <option value="ARCHIVED">Archived</option>
            </Select>
          </label>
          <label className="space-y-1 text-caption text-muted">
            Case
            <Select
              aria-label="Case filter"
              onChange={(e) => set("caseId", e.target.value)}
              value={filters.caseId}
            >
              <option value="all">All cases</option>
              {caseOptions.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.label}
                </option>
              ))}
            </Select>
          </label>
          <label className="space-y-1 text-caption text-muted">
            AI modality
            <Select
              aria-label="AI modality"
              onChange={(e) => set("aiModality", e.target.value)}
              value={filters.aiModality}
            >
              <option value="all">All</option>
              {modalities.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </Select>
          </label>
          <label className="space-y-1 text-caption text-muted">
            Correlation type
            <Select
              aria-label="Correlation type"
              onChange={(e) => set("correlationType", e.target.value)}
              value={filters.correlationType}
            >
              <option value="all">All</option>
              {correlationTypes.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </Select>
          </label>
        </div>
        {filters.selectedSliceId && (
          <p className="mt-3 text-caption text-primary">
            Chart filter active: {filters.selectedSliceId}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
