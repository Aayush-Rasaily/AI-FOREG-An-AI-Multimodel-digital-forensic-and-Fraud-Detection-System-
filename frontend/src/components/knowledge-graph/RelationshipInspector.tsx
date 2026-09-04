import type { GraphRelationship } from "../../types/knowledgeGraph";
import { Badge } from "../ui/Badge";
import { EmptyState } from "../ui/EmptyState";
import { Panel } from "../ui/Panel";

interface RelationshipInspectorProps {
  relationship: GraphRelationship | null;
}

export function RelationshipInspector({
  relationship,
}: RelationshipInspectorProps) {
  return (
    <Panel
      description="Selected relationship confidence, weight, and provenance."
      title="Relationship"
    >
      <div className="space-y-3 p-4 text-xs text-slate-400">
        {!relationship ? (
          <EmptyState
            description="Select an edge label or neighbor link to inspect."
            title="No relationship selected"
          />
        ) : (
          <>
            <div className="flex flex-wrap gap-2">
              <Badge tone="cyan">{relationship.relationship_type}</Badge>
              <Badge tone="neutral">
                {(relationship.confidence * 100).toFixed(0)}%
              </Badge>
              <Badge tone="neutral">
                weight {relationship.relationship_weight.toFixed(2)}
              </Badge>
            </div>
            <p>
              <span className="text-slate-300">{relationship.source_entity_key}</span>
              {" → "}
              <span className="text-slate-300">{relationship.target_entity_key}</span>
            </p>
            <p>
              Source: {relationship.creation_source} · Supports:{" "}
              {relationship.support_count} · Provenance:{" "}
              {relationship.provenance_count}
            </p>
            {relationship.evidence_ids.length ? (
              <p className="font-mono text-[11px]">
                Evidence: {relationship.evidence_ids.join(", ")}
              </p>
            ) : null}
            {relationship.provenance?.length ? (
              <ul className="max-h-32 space-y-1 overflow-y-auto">
                {relationship.provenance.map((item) => (
                  <li key={`${item.source_kind}-${item.source_id}`}>
                    {item.source_kind}: {item.source_id}
                  </li>
                ))}
              </ul>
            ) : null}
          </>
        )}
      </div>
    </Panel>
  );
}
