import type { CoverageMetrics } from "../../types/investigationIntelligence";
import { Panel } from "../ui/Panel";

interface CoveragePanelProps {
  coverage: CoverageMetrics | null;
  investigationScore: number | null;
}

function pct(value: number) {
  return `${(value * 100).toFixed(0)}%`;
}

export function CoveragePanel({
  coverage,
  investigationScore,
}: CoveragePanelProps) {
  if (!coverage) {
    return (
      <Panel description="Investigation coverage metrics." title="Coverage">
        <div className="p-4 text-xs text-slate-500">No coverage yet.</div>
      </Panel>
    );
  }

  const rows: Array<[string, string]> = [
    ["Evidence analyzed", `${coverage.evidence_analyzed}/${coverage.evidence_total}`],
    ["Evidence pending", String(coverage.evidence_pending)],
    ["Timeline", pct(coverage.timeline_coverage)],
    ["Knowledge graph", pct(coverage.knowledge_graph_coverage)],
    ["Correlation", pct(coverage.correlation_coverage)],
    ["Fusion", pct(coverage.fusion_coverage)],
    ["AI", pct(coverage.ai_coverage)],
    ["Metadata", pct(coverage.metadata_completeness)],
    ["Chain of custody", pct(coverage.chain_of_custody_completeness)],
    ["Overall completeness", pct(coverage.overall_completeness)],
    ["Open conflicts", String(coverage.open_conflicts)],
  ];

  return (
    <Panel description="Investigation coverage metrics." title="Coverage">
      <div className="space-y-3 p-4 text-xs text-slate-400">
        {investigationScore != null ? (
          <p className="text-lg text-slate-100">
            Score {investigationScore.toFixed(1)}
          </p>
        ) : null}
        <dl className="grid gap-2 sm:grid-cols-2">
          {rows.map(([label, value]) => (
            <div key={label}>
              <dt className="text-slate-600">{label}</dt>
              <dd className="text-slate-200">{value}</dd>
            </div>
          ))}
        </dl>
      </div>
    </Panel>
  );
}
