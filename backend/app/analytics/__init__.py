"""Phase 9G investigation analytics & operational metrics.

Deterministic aggregation of persisted investigation data.
Never re-runs AI and never performs forecasting or ML.
"""

from backend.app.analytics.service import AnalyticsService

__all__ = ["AnalyticsService"]
