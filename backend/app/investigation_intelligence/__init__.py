"""Phase 9C investigation intelligence & hypothesis engine.

Package name is `investigation_intelligence` because Phase 8C already owns
`backend.app.intelligence` (investigation summaries).
"""

from backend.app.investigation_intelligence.service import (
    InvestigationIntelligenceEngineService,
)

__all__ = ["InvestigationIntelligenceEngineService"]
