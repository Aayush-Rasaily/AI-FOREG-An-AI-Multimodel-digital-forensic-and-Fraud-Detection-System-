import { Link } from "react-router-dom";
import { ArrowLeft, SearchX } from "lucide-react";

import { Button } from "../components/ui/Button";
import { EmptyState } from "../components/ui/EmptyState";

export function NotFoundPage() {
  return (
    <div className="flex min-h-[70vh] items-center justify-center animate-fade-in">
      <EmptyState
        action={
          <div className="flex flex-wrap justify-center gap-2">
            <Link to="/dashboard">
              <Button variant="primary">
                <ArrowLeft aria-hidden="true" size={15} />
                Return to dashboard
              </Button>
            </Link>
            <Button
              onClick={() => window.history.back()}
              type="button"
              variant="secondary"
            >
              Go back
            </Button>
          </div>
        }
        description="The route you requested is not part of the investigation workspace (404)."
        icon={<SearchX aria-hidden="true" size={20} />}
        title="Page not found"
      />
    </div>
  );
}
