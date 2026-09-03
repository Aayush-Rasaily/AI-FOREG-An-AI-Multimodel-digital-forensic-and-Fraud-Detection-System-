import { Link } from "react-router-dom";
import { ArrowLeft, ShieldOff } from "lucide-react";

import { Button } from "../components/ui/Button";
import { EmptyState } from "../components/ui/EmptyState";

export function UnauthorizedPage() {
  return (
    <div className="flex min-h-[70vh] items-center justify-center">
      <EmptyState
        action={
          <Link to="/dashboard">
            <Button variant="primary">
              <ArrowLeft aria-hidden="true" size={15} />
              Return to dashboard
            </Button>
          </Link>
        }
        description="Your account does not have permission to open this area."
        icon={<ShieldOff aria-hidden="true" size={20} />}
        title="Unauthorized"
      />
    </div>
  );
}
