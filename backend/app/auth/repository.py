"""Persistence helpers for authentication entities."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.role import Permission, Role
from backend.app.models.session import RefreshToken, UserSession
from backend.app.models.user import User


class AuthRepository:
    """Query helper for users, roles, sessions, and tokens."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User | None:
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(func.lower(User.username) == username.lower())
        )
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(func.lower(User.email) == email.lower())
        )
        return result.scalar_one_or_none()

    async def list_users(self, *, limit: int, offset: int) -> tuple[list[User], int]:
        total_result = await self.session.execute(select(func.count(User.id)))
        total = int(total_result.scalar_one())
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .order_by(User.username)
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all()), total

    async def list_roles(self) -> list[Role]:
        result = await self.session.execute(
            select(Role)
            .options(selectinload(Role.permissions))
            .order_by(Role.name)
        )
        return list(result.scalars().all())

    async def list_permissions(self) -> list[Permission]:
        result = await self.session.execute(
            select(Permission).order_by(Permission.code)
        )
        return list(result.scalars().all())

    async def get_role_by_name(self, name: str) -> Role | None:
        result = await self.session.execute(
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.name == name)
        )
        return result.scalar_one_or_none()

    async def get_permission_by_code(self, code: str) -> Permission | None:
        result = await self.session.execute(
            select(Permission).where(Permission.code == code)
        )
        return result.scalar_one_or_none()

    async def get_session(self, session_id: UUID) -> UserSession | None:
        result = await self.session.execute(
            select(UserSession).where(UserSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def list_sessions_for_user(self, user_id: UUID) -> list[UserSession]:
        result = await self.session.execute(
            select(UserSession)
            .where(UserSession.user_id == user_id)
            .order_by(UserSession.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_refresh_token(self, token_hash: str) -> RefreshToken | None:
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def add(self, entity: object) -> None:
        self.session.add(entity)

    async def count_users(self) -> int:
        result = await self.session.execute(select(func.count(User.id)))
        return int(result.scalar_one())

    async def count_roles(self) -> int:
        result = await self.session.execute(select(func.count(Role.id)))
        return int(result.scalar_one())

    async def revoke_refresh_tokens(
        self,
        *,
        user_id: UUID,
        session_id: UUID | None = None,
        except_session_id: UUID | None = None,
        now: datetime,
    ) -> None:
        stmt = update(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
        if session_id is not None:
            stmt = stmt.where(RefreshToken.session_id == session_id)
        if except_session_id is not None:
            stmt = stmt.where(RefreshToken.session_id != except_session_id)
        await self.session.execute(stmt.values(revoked_at=now))
