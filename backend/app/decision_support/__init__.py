"""Phase 9D investigation workflow & decision support engine.

Package name is `decision_support` because Phase 8E already owns
`backend.app.workflow` (investigation workflow / collaboration).
"""

from backend.app.decision_support.service import DecisionSupportService

__all__ = ["DecisionSupportService"]
