import { type FormEvent, useState } from "react";

import { collaborationApi } from "../../services/api/collaboration";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { Panel } from "../ui/Panel";
import { Select } from "../ui/Select";

export function ReviewPanel({ caseId }: { caseId: string }) {
  const [resourceId, setResourceId] = useState(caseId);
  const [resourceType, setResourceType] = useState("case_closure");
  const [message, setMessage] = useState<string | null>(null);
  const [reviewId, setReviewId] = useState<string | null>(null);

  async function onRequest(event: FormEvent) {
    event.preventDefault();
    const response = await collaborationApi.createReview({
      case_id: caseId,
      resource_type: resourceType,
      resource_id: resourceId,
    });
    setReviewId(response.data.id);
    setMessage(`Review ${response.data.state}`);
  }

  async function onDecide(decision: string) {
    if (!reviewId) return;
    const response = await collaborationApi.decideReview(reviewId, decision);
    setMessage(`Decision: ${response.data.state}`);
  }

  return (
    <Panel description="Request and decide collaborative reviews." title="Reviews">
      <form className="space-y-2" onSubmit={onRequest}>
        <Select
          onChange={(event) => setResourceType(event.target.value)}
          value={resourceType}
        >
          <option value="case_closure">Case closure</option>
          <option value="report">Report</option>
          <option value="timeline">Timeline</option>
          <option value="fusion">Fusion</option>
          <option value="entity_graph">Entity graph</option>
        </Select>
        <Input
          onChange={(event) => setResourceId(event.target.value)}
          value={resourceId}
        />
        <Button size="sm" type="submit" variant="primary">
          Request review
        </Button>
      </form>
      {reviewId && (
        <div className="mt-3 flex gap-2">
          <Button onClick={() => void onDecide("approve")} size="sm">
            Approve
          </Button>
          <Button
            onClick={() => void onDecide("request_changes")}
            size="sm"
            variant="secondary"
          >
            Request changes
          </Button>
          <Button
            onClick={() => void onDecide("reject")}
            size="sm"
            variant="danger"
          >
            Reject
          </Button>
        </div>
      )}
      {message && <p className="mt-2 text-xs text-slate-400">{message}</p>}
    </Panel>
  );
}
