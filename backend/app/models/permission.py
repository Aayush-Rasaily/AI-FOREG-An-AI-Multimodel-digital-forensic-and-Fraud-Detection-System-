"""SQLAlchemy persistence for permissions.

The Permission ORM class lives in ``backend.app.models.role`` alongside
role assignment tables so metadata is created in one module.
"""

from backend.app.models.role import Permission

__all__ = ["Permission"]
