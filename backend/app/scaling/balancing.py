"""Load-balancing helpers and replica topology hints (Phase 10E)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

StickyMode = Literal["none", "cookie", "ip_hash"]


@dataclass(frozen=True, slots=True)
class LoadBalancingPolicy:
    """Declarative LB policy for reverse proxies / ingress."""

    api_replicas: int = 2
    worker_replicas: int = 2
    sticky_sessions: StickyMode = "none"
    stateless_api: bool = True
    health_path: str = "/api/v1/system/readiness"
    liveness_path: str = "/api/v1/system/liveness"


DEFAULT_LB_POLICY = LoadBalancingPolicy()


def recommend_sticky_sessions(*, uses_local_storage: bool) -> StickyMode:
    """Sticky sessions are only recommended when local disk affinity matters."""

    if uses_local_storage:
        return "cookie"
    return "none"


def balancing_guidance(policy: LoadBalancingPolicy | None = None) -> dict[str, Any]:
    """Return machine-readable LB guidance for docs/ops tooling."""

    active = policy or DEFAULT_LB_POLICY
    return {
        "api_replicas": active.api_replicas,
        "worker_replicas": active.worker_replicas,
        "sticky_sessions": active.sticky_sessions,
        "stateless_api": active.stateless_api,
        "health_path": active.health_path,
        "liveness_path": active.liveness_path,
        "notes": [
            "API pods are designed to be stateless when object storage is used.",
            "Prefer cookie affinity only when evidence remains on local PVCs.",
            "Workers consume queues independently; "
            "do not terminate mid-job without drain.",
        ],
    }
