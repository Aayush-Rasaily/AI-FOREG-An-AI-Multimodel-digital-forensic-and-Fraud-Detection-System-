import { useEffect, useState } from "react";
import { Search } from "lucide-react";

import { EvidenceList } from "../components/evidence/EvidenceList";
import { EvidenceUploadForm } from "../components/evidence/EvidenceUploadForm";
import { PageHeader } from "../components/layout/PageHeader";
import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorState } from "../components/ui/ErrorState";
import { Input } from "../components/ui/Input";
import { LoadingState } from "../components/ui/LoadingState";
import { Select } from "../components/ui/Select";
import { useCasesQuery } from "../hooks/useCases";
import { useCaseEvidenceQuery } from "../hooks/useEvidence";
import { ApiClientError } from "../services/api/client";

export function EvidencePage() {
  const casesQuery = useCasesQuery();
  const [selectedCaseId, setSelectedCaseId] = useState("");
  const evidenceQuery = useCaseEvidenceQuery(selectedCaseId);

  useEffect(() => {
    if (!selectedCaseId && casesQuery.data?.data.items[0]) {
      setSelectedCaseId(casesQuery.data.data.items[0].id);
    }
  }, [casesQuery.data, selectedCaseId]);

  const selectedCase = casesQuery.data?.data.items.find(
    (item) => item.id === selectedCaseId,
  );

  return (
    <div>
      <PageHeader
        description="A controlled index for evidence items, custody records, and source artifacts."
        eyebrow="Evidence registry"
        title="Evidence"
      />
      <Card className="mb-4 flex flex-col gap-3 p-3 sm:flex-row">
        <label className="relative min-w-0 flex-1">
          <span className="sr-only">Search evidence</span>
          <Search
            aria-hidden="true"
            className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-600"
            size={16}
          />
          <Input className="pl-9" placeholder="Search evidence by hash, name, or case" />
        </label>
        <Select
          aria-label="Select case"
          onChange={(event) => setSelectedCaseId(event.target.value)}
          value={selectedCaseId}
        >
          <option value="">Select a case</option>
          {(casesQuery.data?.data.items ?? []).map((item) => (
            <option key={item.id} value={item.id}>
              {item.case_number} · {item.title}
            </option>
          ))}
        </Select>
      </Card>
      {casesQuery.isPending && <LoadingState label="Loading cases" />}
      {casesQuery.isError && (
        <ErrorState
          description={
            casesQuery.error instanceof ApiClientError
              ? casesQuery.error.message
              : "Cases could not be loaded."
          }
          onRetry={() => void casesQuery.refetch()}
        />
      )}
      {casesQuery.isSuccess && !selectedCase && (
        <Card>
          <EmptyState
            description="Create a case before registering original evidence."
            title="No case selected"
          />
        </Card>
      )}
      {selectedCase && (
        <>
          <Card>
            {evidenceQuery.isPending && <LoadingState label="Loading evidence" />}
            {evidenceQuery.isError && (
              <ErrorState
                description="Evidence records could not be loaded."
                onRetry={() => void evidenceQuery.refetch()}
              />
            )}
            {evidenceQuery.isSuccess && (
              <EvidenceList items={evidenceQuery.data.data.items} />
            )}
          </Card>
          <div className="mt-4">
            <EvidenceUploadForm caseId={selectedCase.id} />
          </div>
        </>
      )}
    </div>
  );
}

