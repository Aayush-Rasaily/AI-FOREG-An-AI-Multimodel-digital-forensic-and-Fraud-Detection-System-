"""SQLAlchemy declarative base owned by the infrastructure layer."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for persistence models added in future increments."""
