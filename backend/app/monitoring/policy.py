"""Policy constants and health thresholds for Phase 8D monitoring."""

from __future__ import annotations

ENGINE_VERSION = "8d.1.0"
POLICY_VERSION = "8d.1.0"

# Failure rates (0–1) that escalate health status.
WARNING_FAILURE_RATE = 0.10
DEGRADED_FAILURE_RATE = 0.25
CRITICAL_FAILURE_RATE = 0.50

# Absolute queued/running job backlog thresholds.
WARNING_QUEUE_BACKLOG = 5
DEGRADED_QUEUE_BACKLOG = 20
CRITICAL_QUEUE_BACKLOG = 50

# Inactive case threshold in days (based on updated_at).
INACTIVE_CASE_DAYS = 14
