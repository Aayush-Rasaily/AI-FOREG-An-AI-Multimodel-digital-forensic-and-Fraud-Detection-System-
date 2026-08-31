"""FastAPI dependency providers for transport-layer composition."""

from backend.app.infrastructure.database.session import get_db_session

__all__ = ["get_db_session"]
