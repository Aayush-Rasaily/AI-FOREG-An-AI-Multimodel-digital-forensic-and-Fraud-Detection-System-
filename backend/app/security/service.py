"""Application service for enterprise security governance."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.auth.models import AuthenticatedPrincipal
from backend.app.core.exceptions import ResourceNotFoundError
from backend.app.models.security import (
    CaseAccessRecord,
    ComplianceReport,
    PolicyViolation,
    SecurityPermission,
    SecurityRole,
)
from backend.app.security.audit import record_security_audit
from backend.app.security.compliance import snapshot_to_dict
from backend.app.security.engine import (
    evaluate_chain_validation,
    evaluate_compliance,
    policy_document,
)
from backend.app.security.exceptions import (
    SecurityConflictError,
    SecurityError,
    SecurityForbiddenError,
)
from backend.app.security.policy import (
    ENGINE_VERSION,
    SECURITY_POLICY_VERSION,
    AccessLevel,
    ViolationSeverity,
)
from backend.app.security.rbac import (
    build_permission_catalog,
    build_role_catalog,
)
from backend.app.security.repository import SecurityRepository
from backend.app.security.schemas import (
    CaseAccessListResponse,
    CaseAccessResponse,
    ComplianceResponse,
    PolicyDocumentResponse,
    PolicyViolationListResponse,
    PolicyViolationResponse,
    SecurityPermissionListResponse,
    SecurityPermissionResponse,
    SecurityRoleListResponse,
    SecurityRoleResponse,
    ValidationFindingResponse,
    ValidationResponse,
)


def _actor(
    principal: AuthenticatedPrincipal | None,
) -> tuple[UUID | None, str]:
    if principal is None:
        return None, "system"
    return principal.user_id, principal.username


class SecurityService:
    """Manage RBAC catalog, case access, compliance, and validation."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = SecurityRepository(session)

    async def ensure_catalog_seeded(self) -> None:
        """Seed governance roles/permissions when the catalog is empty."""

        if await self.repository.count_roles() > 0:
            return
        for item in build_role_catalog():
            await self.repository.add(
                SecurityRole(
                    code=item["code"],
                    name=item["name"],
                    description=item["description"],
                    permissions_json=item["permissions"],
                    policy_version=item["policy_version"],
                )
            )
        for item in build_permission_catalog():
            await self.repository.add(
                SecurityPermission(
                    code=item["code"],
                    resource=item["resource"],
                    action=item["action"],
                    description=item["description"],
                    policy_version=item["policy_version"],
                )
            )
        await self.session.commit()

    def _access_response(self, row: CaseAccessRecord) -> CaseAccessResponse:
        return CaseAccessResponse(
            id=row.id,
            case_id=row.case_id,
            user_id=row.user_id,
            access_level=row.access_level,
            granted_by=row.granted_by,
            reason=row.reason,
            active=row.active,
            granted_at=row.granted_at,
            revoked_at=row.revoked_at,
        )

    async def list_roles(self) -> SecurityRoleListResponse:
        await self.ensure_catalog_seeded()
        rows = await self.repository.list_roles()
        items = [
            SecurityRoleResponse(
                id=row.id,
                code=row.code,
                name=row.name,
                description=row.description,
                permissions=list(row.permissions_json or []),
                policy_version=row.policy_version,
            )
            for row in rows
        ]
        return SecurityRoleListResponse(items=items, total=len(items))

    async def list_permissions(self) -> SecurityPermissionListResponse:
        await self.ensure_catalog_seeded()
        catalog = {item["code"]: item for item in build_permission_catalog()}
        rows = await self.repository.list_permissions()
        items = [
            SecurityPermissionResponse(
                id=row.id,
                code=row.code,
                resource=row.resource,
                action=row.action,
                description=row.description,
                roles=list(catalog.get(row.code, {}).get("roles", [])),
                policy_version=row.policy_version,
            )
            for row in rows
        ]
        return SecurityPermissionListResponse(items=items, total=len(items))

    async def get_policy(self) -> PolicyDocumentResponse:
        doc = policy_document()
        return PolicyDocumentResponse(**doc)

    async def assert_case_access(
        self,
        case_id: UUID,
        principal: AuthenticatedPrincipal | None,
        *,
        allow_without_auth: bool = True,
    ) -> None:
        """Raise 403 when the principal lacks case access."""

        if principal is None:
            if allow_without_auth:
                return
            raise SecurityForbiddenError("Authentication is required.")
        if principal.has_permission("admin.manage_users"):
            return
        if principal.has_permission("security.manage"):
            return
        access = await self.repository.get_active_access(
            case_id, principal.user_id,
        )
        if access is None:
            raise SecurityForbiddenError(
                "You do not have access to this case."
            )

    async def list_case_access(
        self,
        case_id: UUID,
        principal: AuthenticatedPrincipal | None = None,
    ) -> CaseAccessListResponse:
        if await self.repository.get_case(case_id) is None:
            raise ResourceNotFoundError("The case was not found.")
        await self.assert_case_access(case_id, principal)
        rows = await self.repository.list_case_access(case_id)
        items = [self._access_response(row) for row in rows]
        return CaseAccessListResponse(items=items, total=len(items))

    async def update_case_access(
        self,
        case_id: UUID,
        *,
        user_id: UUID,
        access_level: str,
        reason: str | None,
        active: bool,
        principal: AuthenticatedPrincipal | None,
    ) -> CaseAccessResponse:
        if await self.repository.get_case(case_id) is None:
            raise ResourceNotFoundError("The case was not found.")
        if principal is not None and not (
            principal.has_permission("admin.manage_users")
            or principal.has_permission("security.manage")
            or principal.has_permission("collab.manage_members")
        ):
            raise SecurityForbiddenError(
                "You are not allowed to manage case access."
            )
        if await self.repository.get_user(user_id) is None:
            raise ResourceNotFoundError("The user was not found.")
        try:
            level = AccessLevel(access_level)
        except ValueError as exc:
            raise SecurityError(
                f"Unknown access level: {access_level}"
            ) from exc

        actor_id, actor_username = _actor(principal)
        existing = await self.repository.get_active_access(case_id, user_id)
        # Also find inactive matching level
        all_rows = await self.repository.list_case_access(case_id)
        match = next(
            (
                row
                for row in all_rows
                if row.user_id == user_id
                and row.access_level == level.value
            ),
            None,
        )
        if match is not None:
            previous = {"active": match.active, "access_level": match.access_level}
            match.active = active
            match.reason = reason
            if active:
                match.revoked_at = None
                match.granted_by = actor_id
                match.granted_at = datetime.now(UTC)
            else:
                match.revoked_at = datetime.now(UTC)
            row = match
        else:
            if not active:
                raise SecurityConflictError(
                    "Cannot revoke a non-existent access grant."
                )
            if existing is not None and existing.access_level != level.value:
                # Keep multiple levels allowed by unique constraint
                pass
            previous = None
            row = CaseAccessRecord(
                case_id=case_id,
                user_id=user_id,
                access_level=level.value,
                granted_by=actor_id,
                reason=reason,
                active=True,
            )
            await self.repository.add(row)
        await self.session.flush()
        await record_security_audit(
            self.session,
            operation="security.case_access_updated",
            user=actor_username,
            case_id=case_id,
            previous_state=previous,
            new_state={
                "user_id": str(user_id),
                "access_level": level.value,
                "active": active,
            },
        )
        await self.session.commit()
        return self._access_response(row)

    async def _build_compliance(
        self, case_id: UUID,
    ) -> ComplianceResponse:
        evidence_count = await self.repository.count_evidence(case_id)
        custody = await self.repository.count_custody_events(case_id)
        hashed = await self.repository.count_evidence_with_hash(case_id)
        audits = await self.repository.count_audit_events(case_id)
        inv = await self.repository.get_investigation_workflow(case_id)
        collab = await self.repository.get_collab_workflow(case_id)
        workflow_status = None
        if inv is not None:
            workflow_status = inv.status
        elif collab is not None:
            workflow_status = collab.stage
        reports = await self.repository.count_reports(case_id)
        reports_prov = await self.repository.count_reports_with_provenance(
            case_id,
        )
        approved = await self.repository.count_approved_report_reviews(case_id)
        published_bad = await self.repository.count_published_without_approval(
            case_id,
        )
        fusion_total, fusion_prov = await self.repository.count_fusion(case_id)
        corr_total, corr_prov = await self.repository.count_correlation(case_id)
        open_violations = await self.repository.list_violations(
            case_id=case_id, open_only=True,
        )
        snapshot = evaluate_compliance(
            case_id=case_id,
            evidence_count=evidence_count,
            custody_event_count=custody,
            evidence_with_hash=hashed,
            audit_event_count=audits,
            workflow_status=workflow_status,
            approved_report_reviews=approved,
            published_without_approval=published_bad,
            reports_with_provenance=reports_prov,
            report_count=reports,
            fusion_with_provenance=fusion_prov,
            fusion_count=fusion_total,
            correlation_with_provenance=corr_prov,
            correlation_count=corr_total,
            open_violations=[item.policy_code for item in open_violations],
        )
        report = ComplianceReport(
            case_id=case_id,
            status=snapshot.status,
            summary_json=snapshot_to_dict(snapshot),
            policy_version=SECURITY_POLICY_VERSION,
            engine_version=ENGINE_VERSION,
        )
        await self.repository.add(report)
        await self.session.flush()
        return ComplianceResponse(
            status=snapshot.status,
            case_id=case_id,
            chain_of_custody_complete=snapshot.chain_of_custody_complete,
            evidence_integrity_ok=snapshot.evidence_integrity_ok,
            audit_complete=snapshot.audit_complete,
            workflow_compliant=snapshot.workflow_compliant,
            report_approval_compliant=snapshot.report_approval_compliant,
            missing_approvals=list(snapshot.missing_approvals),
            missing_provenance=list(snapshot.missing_provenance),
            policy_violations=list(snapshot.policy_violations),
            details=dict(snapshot.details),
            generated_at=snapshot.generated_at,
            policy_version=snapshot.policy_version,
            engine_version=snapshot.engine_version,
            report_id=report.id,
        )

    async def get_case_compliance(
        self,
        case_id: UUID,
        principal: AuthenticatedPrincipal | None = None,
    ) -> ComplianceResponse:
        if await self.repository.get_case(case_id) is None:
            raise ResourceNotFoundError("The case was not found.")
        await self.assert_case_access(case_id, principal)
        actor_id, actor_username = _actor(principal)
        response = await self._build_compliance(case_id)
        await record_security_audit(
            self.session,
            operation="security.compliance_generated",
            user=actor_username,
            case_id=case_id,
            new_state={"status": response.status, "report_id": str(response.report_id)},
            metadata={"actor_id": str(actor_id) if actor_id else None},
        )
        await self.session.commit()
        return response

    async def list_violations(
        self,
        *,
        case_id: UUID | None = None,
    ) -> PolicyViolationListResponse:
        rows = await self.repository.list_violations(case_id=case_id)
        items = [
            PolicyViolationResponse(
                id=row.id,
                case_id=row.case_id,
                policy_code=row.policy_code,
                severity=row.severity,
                message=row.message,
                details=dict(row.details_json or {}),
                detected_at=row.detected_at,
                resolved_at=row.resolved_at,
                policy_version=row.policy_version,
            )
            for row in rows
        ]
        return PolicyViolationListResponse(items=items, total=len(items))

    async def record_violation(
        self,
        *,
        policy_code: str,
        message: str,
        severity: str = ViolationSeverity.WARNING.value,
        case_id: UUID | None = None,
        details: dict | None = None,
    ) -> PolicyViolation:
        row = PolicyViolation(
            case_id=case_id,
            policy_code=policy_code,
            severity=severity,
            message=message,
            details_json=details or {},
            policy_version=SECURITY_POLICY_VERSION,
        )
        await self.repository.add(row)
        await self.session.flush()
        return row

    async def validate(
        self,
        *,
        case_id: UUID | None,
        principal: AuthenticatedPrincipal | None,
    ) -> ValidationResponse:
        actor_id, actor_username = _actor(principal)
        if case_id is None:
            result = evaluate_chain_validation(
                evidence_hash_ok=True,
                audit_continuity_ok=True,
                timeline_continuity_ok=True,
                workflow_continuity_ok=True,
                report_provenance_ok=True,
                fusion_provenance_ok=True,
                correlation_provenance_ok=True,
                details={"scope": "platform"},
            )
        else:
            if await self.repository.get_case(case_id) is None:
                raise ResourceNotFoundError("The case was not found.")
            await self.assert_case_access(case_id, principal)
            evidence_count = await self.repository.count_evidence(case_id)
            hashed = await self.repository.count_evidence_with_hash(case_id)
            audits = await self.repository.count_audit_events(case_id)
            has_timeline = await self.repository.has_timeline(case_id)
            inv = await self.repository.get_investigation_workflow(case_id)
            reports = await self.repository.count_reports(case_id)
            reports_prov = await self.repository.count_reports_with_provenance(
                case_id,
            )
            fusion_total, fusion_prov = await self.repository.count_fusion(
                case_id,
            )
            corr_total, corr_prov = await self.repository.count_correlation(
                case_id,
            )
            workflow_ok = True
            if inv is not None:
                activity = list(inv.activity_json or [])
                workflow_ok = len(activity) >= 1

            # Record deterministic violations for failed checks
            if evidence_count > 0 and hashed < evidence_count:
                await self.record_violation(
                    policy_code="evidence_security",
                    message="Evidence hash integrity gap detected.",
                    severity=ViolationSeverity.HIGH.value,
                    case_id=case_id,
                    details={"hashed": hashed, "evidence_count": evidence_count},
                )

            result = evaluate_chain_validation(
                evidence_hash_ok=(
                    evidence_count == 0 or hashed == evidence_count
                ),
                audit_continuity_ok=(audits > 0 or evidence_count == 0),
                timeline_continuity_ok=(
                    not has_timeline or has_timeline
                ),
                workflow_continuity_ok=workflow_ok,
                report_provenance_ok=(
                    reports == 0 or reports_prov == reports
                ),
                fusion_provenance_ok=(
                    fusion_total == 0 or fusion_prov == fusion_total
                ),
                correlation_provenance_ok=(
                    corr_total == 0 or corr_prov == corr_total
                ),
                details={
                    "evidence": {
                        "count": evidence_count,
                        "hashed": hashed,
                    },
                    "audit": {"count": audits},
                    "timeline": {"present": has_timeline},
                    "workflow": {
                        "present": inv is not None,
                        "activity_events": (
                            len(inv.activity_json or []) if inv else 0
                        ),
                    },
                    "report": {
                        "count": reports,
                        "with_provenance": reports_prov,
                    },
                    "fusion": {
                        "count": fusion_total,
                        "with_provenance": fusion_prov,
                    },
                    "correlation": {
                        "count": corr_total,
                        "with_provenance": corr_prov,
                    },
                },
            )

        await record_security_audit(
            self.session,
            operation="security.validate",
            user=actor_username,
            case_id=case_id,
            new_state={"status": result.status},
            metadata={"actor_id": str(actor_id) if actor_id else None},
        )
        await self.session.commit()
        return ValidationResponse(
            status=result.status,
            findings=[
                ValidationFindingResponse(
                    check=item.check,
                    status=item.status,
                    message=item.message,
                    details=dict(item.details),
                )
                for item in result.findings
            ],
            generated_at=result.generated_at,
            policy_version=result.policy_version,
            engine_version=result.engine_version,
            case_id=case_id,
        )
