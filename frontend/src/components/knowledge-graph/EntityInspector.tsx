import type { GraphEntity } from "../../types/knowledgeGraph";
import { Badge } from "../ui/Badge";
import { EmptyState } from "../ui/EmptyState";
import { LoadingState } from "../ui/LoadingState";
import { Panel } from "../ui/Panel";
import { useGraphEntityQuery } from "../../hooks/useKnowledgeGraph";

interface EntityInspectorProps {
  entityId: string | null;
  fallback?: GraphEntity | null;
}

export function EntityInspector({ entityId, fallback }: EntityInspectorProps) {
  const query = useGraphEntityQuery(entityId);
  const entity = query.data?.data ?? fallback ?? null;

  return (
    <Panel description="Selected entity details and provenance." title="Entity">
      <div className="space-y-3 p-4 text-xs text-slate-400">
        {!entityId && !fallback ? (
          <EmptyState
            description="Select a node in the graph to inspect it."
            title="No entity selected"
          />
        ) : null}
        {query.isLoading && entityId ? (
          <LoadingState label="Loading entity" />
        ) : null}
        {entity ? (
          <>
            <div className="flex flex-wrap gap-2">
              <Badge tone="cyan">{entity.entity_type}</Badge>
              <Badge tone="neutral">
                {(entity.confidence * 100).toFixed(0)}% confidence
              </Badge>
            </div>
            <p className="text-sm text-slate-200">{entity.display_name}</p>
            <p className="font-mono text-[11px] text-slate-500">
              {entity.normalized_key}
            </p>
            {entity.evidence_ids.length ? (
              <div>
                <p className="mb-1 text-[11px] uppercase tracking-wide text-slate-600">
                  Evidence links
                </p>
                <ul className="space-y-1">
                  {entity.evidence_ids.map((id) => (
                    <li className="font-mono text-slate-300" key={id}>
                      {id}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            {entity.provenance?.length ? (
              <div>
                <p className="mb-1 text-[11px] uppercase tracking-wide text-slate-600">
                  Provenance
                </p>
                <ul className="max-h-40 space-y-1 overflow-y-auto">
                  {entity.provenance.map((item) => (
                    <li key={`${item.source_kind}-${item.source_id}`}>
                      <span className="text-slate-300">{item.source_kind}</span>:{" "}
                      {item.source_id}
                      {item.timeline_id ? ` · timeline ${item.timeline_id}` : ""}
                      {item.correlation_id
                        ? ` · correlation ${item.correlation_id}`
                        : ""}
                      {item.fusion_id ? ` · fusion ${item.fusion_id}` : ""}
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <EmptyState
                description="No provenance rows were returned for this entity."
                title="No provenance"
              />
            )}
          </>
        ) : null}
      </div>
    </Panel>
  );
}
