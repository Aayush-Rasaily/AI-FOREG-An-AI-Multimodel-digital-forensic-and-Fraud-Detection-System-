import { SearchX } from "lucide-react";

import { EmptyState } from "./EmptyState";

export function NotFoundState() {
  return (
    <EmptyState
      description="The requested investigation workspace or route does not exist."
      icon={<SearchX aria-hidden="true" size={20} />}
      title="Workspace not found"
    />
  );
}

