"""Application service for authentication, users, and sessions."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.auth.exceptions import (
    AccountLockedError,
    AuthConflictError,
    AuthenticationError,
    AuthorizationError,
    PasswordPolicyError,
)
from backend.app.auth.hashing import hash_password, needs_rehash, verify_password
from backend.app.auth.jwt import decode_token, encode_token
from backend.app.auth.models import AuthenticatedPrincipal
from backend.app.auth.permissions import PERMISSION_DESCRIPTIONS, PermissionCode
from backend.app.auth.policy import LOCKOUT_MINUTES, MAX_FAILED_LOGINS
from backend.app.auth.repository import AuthRepository
from backend.app.auth.roles import (
    BUILTIN_ROLES,
    ROLE_ADMINISTRATOR,
    ROLE_DESCRIPTIONS,
    ROLE_PERMISSIONS,
)
from backend.app.auth.schemas import (
    PermissionResponse,
    RoleResponse,
    SessionListResponse,
    SessionResponse,
    TokenResponse,
    UserListResponse,
    UserResponse,
)
from backend.app.auth.security import (
    assert_ip_allowed,
    clear_ip_failures,
    parse_user_agent,
    register_ip_failure,
    validate_password,
    validate_username,
)
from backend.app.core.config import Settings
from backend.app.core.exceptions import ResourceNotFoundError
from backend.app.models.role import Permission, Role
from backend.app.models.session import RefreshToken, UserSession
from backend.app.models.user import User


def _token_hash(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


class AuthService:
    """Manage identity, sessions, tokens, and RBAC administration."""

    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.repository = AuthRepository(session)

    def _jwt_secret(self) -> str:
        secret = self.settings.jwt_secret
        if secret is None:
            raise AuthenticationError("Authentication is not configured.")
        return secret.get_secret_value()

    def _access_minutes(self) -> int:
        return int(self.settings.auth_access_token_minutes)

    def _refresh_days(self, remember_me: bool) -> int:
        if remember_me:
            return int(self.settings.auth_remember_me_days)
        return int(self.settings.auth_refresh_token_days)

    async def ensure_rbac_seeded(self) -> None:
        """Create built-in roles and permissions when missing."""

        if await self.repository.count_roles() > 0:
            return
        permission_map: dict[str, Permission] = {}
        for code in PermissionCode:
            record = Permission(
                code=code.value,
                description=PERMISSION_DESCRIPTIONS[code.value],
            )
            await self.repository.add(record)
            permission_map[code.value] = record
        await self.session.flush()
        for role_name in BUILTIN_ROLES:
            role = Role(
                name=role_name,
                description=ROLE_DESCRIPTIONS[role_name],
                is_system=True,
            )
            codes = ROLE_PERMISSIONS[role_name]
            role.permissions = [permission_map[code] for code in sorted(codes)]
            await self.repository.add(role)
        await self.session.flush()

    async def ensure_seeded(self) -> None:
        """Create built-in roles, permissions, and optional bootstrap admin."""

        await self.ensure_rbac_seeded()
        bootstrap_password = self.settings.auth_bootstrap_password
        if (
            bootstrap_password is not None
            and await self.repository.count_users() == 0
        ):
            await self._create_user_record(
                username=self.settings.auth_bootstrap_username,
                password=bootstrap_password.get_secret_value(),
                display_name="Administrator",
                email=None,
                role_names=[ROLE_ADMINISTRATOR],
                is_active=True,
            )
        await self.session.commit()

    async def _create_user_record(
        self,
        *,
        username: str,
        password: str,
        display_name: str,
        email: str | None,
        role_names: list[str],
        is_active: bool,
    ) -> User:
        username = validate_username(username)
        validate_password(password)
        if await self.repository.get_user_by_username(username) is not None:
            raise AuthConflictError("That username is already registered.")
        if email and await self.repository.get_user_by_email(email) is not None:
            raise AuthConflictError("That email is already registered.")
        names = role_names or ["Viewer"]
        roles = await self._load_roles(names)
        user = User(
            username=username,
            email=email,
            display_name=display_name.strip(),
            password_hash=hash_password(password),
            is_active=is_active,
            roles=roles,
        )
        await self.repository.add(user)
        await self.session.flush()
        return user

    def _principal_from_user(
        self, user: User, session_id: UUID,
    ) -> AuthenticatedPrincipal:
        roles = tuple(sorted(role.name for role in user.roles))
        permissions: set[str] = set()
        for role in user.roles:
            permissions.update(item.code for item in role.permissions)
        return AuthenticatedPrincipal(
            user_id=user.id,
            username=user.username,
            display_name=user.display_name,
            email=user.email,
            roles=roles,
            permissions=frozenset(permissions),
            session_id=session_id,
            is_active=user.is_active,
        )

    def _user_response(self, user: User) -> UserResponse:
        principal = self._principal_from_user(user, UUID(int=0))
        return UserResponse(
            id=user.id,
            username=user.username,
            display_name=user.display_name,
            email=user.email,
            is_active=user.is_active,
            is_locked=user.is_locked,
            roles=list(principal.roles),
            permissions=sorted(principal.permissions),
            last_login_at=user.last_login_at,
            created_at=user.created_at,
        )

    def _issue_tokens(
        self, user: User, session_row: UserSession, remember_me: bool,
    ) -> TokenResponse:
        secret = self._jwt_secret()
        algorithm = self.settings.jwt_algorithm
        access_delta = timedelta(minutes=self._access_minutes())
        refresh_delta = timedelta(days=self._refresh_days(remember_me))
        access = encode_token(
            secret=secret,
            algorithm=algorithm,
            subject=user.id,
            session_id=session_row.id,
            token_type="access",
            expires_delta=access_delta,
        )
        refresh = encode_token(
            secret=secret,
            algorithm=algorithm,
            subject=user.id,
            session_id=session_row.id,
            token_type="refresh",
            expires_delta=refresh_delta,
        )
        return TokenResponse(
            access_token=access,
            refresh_token=refresh,
            expires_in=self._access_minutes() * 60,
            user=self._user_response(user),
        )

    async def login(
        self,
        *,
        username: str,
        password: str,
        remember_me: bool,
        ip_address: str | None,
        user_agent: str | None,
    ) -> TokenResponse:
        """Authenticate a user and open a session."""

        await self.ensure_seeded()
        assert_ip_allowed(ip_address)
        user = await self.repository.get_user_by_username(username)
        if user is None:
            register_ip_failure(ip_address)
            raise AuthenticationError("Invalid username or password.")
        now = datetime.now(UTC)
        if user.locked_until is not None and _aware(user.locked_until) > now:
            user.is_locked = True
            raise AccountLockedError(
                "This account is locked after too many failed sign-in attempts."
            )
        if user.is_locked:
            raise AccountLockedError("This account is locked.")
        if not user.is_active:
            raise AuthenticationError("This account is disabled.")
        if not verify_password(password, user.password_hash):
            user.failed_login_count += 1
            if user.failed_login_count >= MAX_FAILED_LOGINS:
                user.is_locked = True
                user.locked_until = now + timedelta(minutes=LOCKOUT_MINUTES)
            register_ip_failure(ip_address)
            await self.session.commit()
            raise AuthenticationError("Invalid username or password.")

        user.failed_login_count = 0
        user.is_locked = False
        user.locked_until = None
        user.last_login_at = now
        if needs_rehash(user.password_hash):
            user.password_hash = hash_password(password)
        browser, device = parse_user_agent(user_agent)
        refresh_days = self._refresh_days(remember_me)
        session_row = UserSession(
            user_id=user.id,
            last_activity_at=now,
            expires_at=now + timedelta(days=refresh_days),
            device_name=device,
            browser=browser,
            ip_address=ip_address,
            user_agent=user_agent,
            remember_me=remember_me,
        )
        await self.repository.add(session_row)
        await self.session.flush()
        tokens = self._issue_tokens(user, session_row, remember_me)
        refresh_row = RefreshToken(
            user_id=user.id,
            session_id=session_row.id,
            token_hash=_token_hash(tokens.refresh_token),
            expires_at=session_row.expires_at,
        )
        await self.repository.add(refresh_row)
        clear_ip_failures(ip_address)
        await self.session.commit()
        return tokens

    async def refresh(self, refresh_token: str) -> TokenResponse:
        """Rotate refresh and access tokens for a valid session."""

        payload = decode_token(
            token=refresh_token,
            secret=self._jwt_secret(),
            algorithm=self.settings.jwt_algorithm,
        )
        if payload.get("typ") != "refresh":
            raise AuthenticationError("The refresh token is invalid.")
        stored = await self.repository.get_refresh_token(_token_hash(refresh_token))
        now = datetime.now(UTC)
        if stored is None or stored.revoked_at is not None:
            raise AuthenticationError("The refresh token is invalid.")
        if _aware(stored.expires_at) <= now:
            raise AuthenticationError("The refresh token has expired.")
        session_row = await self.repository.get_session(stored.session_id)
        if (
            session_row is None
            or session_row.revoked_at is not None
            or _aware(session_row.expires_at) <= now
        ):
            raise AuthenticationError("The session is no longer valid.")
        user = await self.repository.get_user_by_id(session_row.user_id)
        if user is None or not user.is_active or user.is_locked:
            raise AuthenticationError("The account is not available.")
        stored.revoked_at = now
        session_row.last_activity_at = now
        tokens = self._issue_tokens(user, session_row, session_row.remember_me)
        await self.repository.add(
            RefreshToken(
                user_id=user.id,
                session_id=session_row.id,
                token_hash=_token_hash(tokens.refresh_token),
                expires_at=session_row.expires_at,
            )
        )
        await self.session.commit()
        return tokens

    async def resolve_access_token(
        self, token: str,
    ) -> AuthenticatedPrincipal:
        """Validate an access token and return the active principal."""

        payload = decode_token(
            token=token,
            secret=self._jwt_secret(),
            algorithm=self.settings.jwt_algorithm,
        )
        if payload.get("typ") != "access":
            raise AuthenticationError("The access token is invalid.")
        session_id = UUID(str(payload["sid"]))
        user_id = UUID(str(payload["sub"]))
        session_row = await self.repository.get_session(session_id)
        now = datetime.now(UTC)
        if (
            session_row is None
            or session_row.user_id != user_id
            or session_row.revoked_at is not None
            or _aware(session_row.expires_at) <= now
        ):
            raise AuthenticationError("The session is no longer valid.")
        user = await self.repository.get_user_by_id(user_id)
        if user is None or not user.is_active:
            raise AuthenticationError("The account is not available.")
        if user.is_locked:
            raise AccountLockedError("This account is locked.")
        session_row.last_activity_at = now
        await self.session.commit()
        return self._principal_from_user(user, session_row.id)

    async def logout(
        self,
        principal: AuthenticatedPrincipal,
        refresh_token: str | None = None,
    ) -> None:
        """Revoke the current session and optional refresh token."""

        now = datetime.now(UTC)
        session_row = await self.repository.get_session(principal.session_id)
        if session_row is not None and session_row.revoked_at is None:
            session_row.revoked_at = now
        await self.repository.revoke_refresh_tokens(
            user_id=principal.user_id,
            session_id=principal.session_id,
            now=now,
        )
        if refresh_token:
            stored = await self.repository.get_refresh_token(_token_hash(refresh_token))
            if stored is not None and stored.user_id == principal.user_id:
                stored.revoked_at = now
        await self.session.commit()

    async def change_password(
        self,
        principal: AuthenticatedPrincipal,
        current_password: str,
        new_password: str,
    ) -> None:
        """Replace the current user's password and revoke other sessions."""

        validate_password(new_password)
        user = await self.repository.get_user_by_id(principal.user_id)
        if user is None:
            raise ResourceNotFoundError("The user was not found.")
        if not verify_password(current_password, user.password_hash):
            raise AuthenticationError("The current password is incorrect.")
        if current_password == new_password:
            raise PasswordPolicyError("The new password must be different.")
        user.password_hash = hash_password(new_password)
        user.password_changed_at = datetime.now(UTC)
        await self._revoke_other_sessions(principal)
        await self.session.commit()

    async def me(self, principal: AuthenticatedPrincipal) -> UserResponse:
        user = await self.repository.get_user_by_id(principal.user_id)
        if user is None:
            raise ResourceNotFoundError("The user was not found.")
        return self._user_response(user)

    async def create_user(
        self,
        *,
        username: str,
        password: str,
        display_name: str,
        email: str | None,
        role_names: list[str],
        is_active: bool,
    ) -> UserResponse:
        await self.ensure_rbac_seeded()
        user = await self._create_user_record(
            username=username,
            password=password,
            display_name=display_name,
            email=email,
            role_names=role_names,
            is_active=is_active,
        )
        await self.session.commit()
        loaded = await self.repository.get_user_by_id(user.id)
        if loaded is None:
            raise ResourceNotFoundError("The user was not found.")
        return self._user_response(loaded)

    async def list_users(self, *, limit: int, offset: int) -> UserListResponse:
        items, total = await self.repository.list_users(limit=limit, offset=offset)
        return UserListResponse(
            items=[self._user_response(item) for item in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_user(self, user_id: UUID) -> UserResponse:
        user = await self.repository.get_user_by_id(user_id)
        if user is None:
            raise ResourceNotFoundError("The user was not found.")
        return self._user_response(user)

    async def update_user(
        self,
        user_id: UUID,
        *,
        display_name: str | None,
        email: str | None,
        is_active: bool | None,
        role_names: list[str] | None,
    ) -> UserResponse:
        user = await self.repository.get_user_by_id(user_id)
        if user is None:
            raise ResourceNotFoundError("The user was not found.")
        if display_name is not None:
            user.display_name = display_name.strip()
        if email is not None:
            if email:
                existing = await self.repository.get_user_by_email(email)
                if existing is not None and existing.id != user.id:
                    raise AuthConflictError("That email is already registered.")
            user.email = email or None
        if is_active is not None:
            user.is_active = is_active
            if not is_active:
                await self._revoke_all_sessions(user.id)
        if role_names is not None:
            user.roles = await self._load_roles(role_names)
        await self.session.commit()
        loaded = await self.repository.get_user_by_id(user.id)
        if loaded is None:
            raise ResourceNotFoundError("The user was not found.")
        return self._user_response(loaded)

    async def delete_user(self, user_id: UUID) -> None:
        user = await self.repository.get_user_by_id(user_id)
        if user is None:
            raise ResourceNotFoundError("The user was not found.")
        user.is_active = False
        await self._revoke_all_sessions(user.id)
        await self.session.commit()

    async def list_roles(self) -> list[RoleResponse]:
        await self.ensure_seeded()
        roles = await self.repository.list_roles()
        return [
            RoleResponse(
                id=role.id,
                name=role.name,
                description=role.description,
                is_system=role.is_system,
                permissions=sorted(item.code for item in role.permissions),
            )
            for role in roles
        ]

    async def list_permissions(self) -> list[PermissionResponse]:
        await self.ensure_seeded()
        permissions = await self.repository.list_permissions()
        return [
            PermissionResponse(code=item.code, description=item.description)
            for item in permissions
        ]

    async def list_sessions(
        self,
        principal: AuthenticatedPrincipal,
        *,
        all_users: bool,
    ) -> SessionListResponse:
        if all_users:
            if not principal.has_permission(PermissionCode.ADMIN_MANAGE_USERS):
                raise AuthorizationError("Administrator access is required.")
            users, _ = await self.repository.list_users(limit=500, offset=0)
            rows: list[UserSession] = []
            for user in users:
                rows.extend(await self.repository.list_sessions_for_user(user.id))
        else:
            rows = await self.repository.list_sessions_for_user(principal.user_id)
        items = [
            SessionResponse(
                id=row.id,
                user_id=row.user_id,
                created_at=row.created_at,
                last_activity_at=row.last_activity_at,
                expires_at=row.expires_at,
                device_name=row.device_name,
                browser=row.browser,
                ip_address=row.ip_address,
                remember_me=row.remember_me,
                revoked=row.revoked_at is not None,
                current=row.id == principal.session_id,
            )
            for row in rows
        ]
        return SessionListResponse(items=items, total=len(items))

    async def revoke_session(
        self, principal: AuthenticatedPrincipal, session_id: UUID,
    ) -> None:
        session_row = await self.repository.get_session(session_id)
        if session_row is None:
            raise ResourceNotFoundError("The session was not found.")
        is_owner = session_row.user_id == principal.user_id
        is_admin = principal.has_permission(PermissionCode.ADMIN_MANAGE_USERS)
        if not is_owner and not is_admin:
            raise AuthorizationError("You cannot revoke that session.")
        if session_row.revoked_at is None:
            session_row.revoked_at = datetime.now(UTC)
        await self.session.commit()

    async def revoke_all_sessions(self, principal: AuthenticatedPrincipal) -> None:
        await self._revoke_all_sessions(principal.user_id)
        await self.session.commit()

    async def _revoke_other_sessions(
        self, principal: AuthenticatedPrincipal,
    ) -> None:
        now = datetime.now(UTC)
        now = datetime.now(UTC)
        for row in await self.repository.list_sessions_for_user(principal.user_id):
            if row.id != principal.session_id and row.revoked_at is None:
                row.revoked_at = now
        await self.repository.revoke_refresh_tokens(
            user_id=principal.user_id,
            except_session_id=principal.session_id,
            now=now,
        )

    async def _revoke_all_sessions(self, user_id: UUID) -> None:
        now = datetime.now(UTC)
        for row in await self.repository.list_sessions_for_user(user_id):
            if row.revoked_at is None:
                row.revoked_at = now
        await self.repository.revoke_refresh_tokens(user_id=user_id, now=now)

    async def _load_roles(self, role_names: list[str]) -> list[Role]:
        roles: list[Role] = []
        for name in role_names:
            role = await self.repository.get_role_by_name(name)
            if role is None:
                raise ResourceNotFoundError(f"Unknown role: {name}")
            roles.append(role)
        return roles
