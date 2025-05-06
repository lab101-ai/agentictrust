from __future__ import annotations

from typing import List, Dict, Any, Optional
from datetime import datetime
from app.db.models import DelegationGrant, Agent, User
from app.db import db_session
from app.db.models.audit.delegation_audit import DelegationAuditLog

class DelegationEngine:
    """Business logic around DelegationGrant lifecycle & validation."""

    # ---------------------------------------------------------------------
    # CRUD helpers
    # ---------------------------------------------------------------------
    def create_grant(
        self,
        *,
        principal_type: str,
        principal_id: str,
        delegate_id: str,
        scope: List[str],
        max_depth: int = 1,
        constraints: Optional[Dict[str, Any]] = None,
        ttl_hours: int = 24,
    ) -> Dict[str, Any]:
        grant = DelegationGrant.create(
            principal_type=principal_type,
            principal_id=principal_id,
            delegate_id=delegate_id,
            scope=scope,
            max_depth=max_depth,
            constraints=constraints,
            ttl_hours=ttl_hours,
        )
        DelegationAuditLog.log_event(
            grant_id=grant.grant_id,
            action="created",
            principal_id=principal_id,
            delegate_id=delegate_id,
            scope=scope,
        )
        return grant.to_dict()

    def revoke_grant(self, grant_id: str, principal_id: Optional[str] = None) -> None:
        grant = DelegationGrant.query.get(grant_id)
        if not grant:
            raise ValueError("grant not found")
        if principal_id and grant.principal_id != principal_id:
            raise ValueError("principal mismatch")
        grant.revoke()
        DelegationAuditLog.log_event(
            grant_id=grant_id,
            action="revoked",
            principal_id=grant.principal_id,
            delegate_id=grant.delegate_id,
            scope=grant.scope,
        )

    def get_grant(self, grant_id: str) -> Dict[str, Any]:
        grant = DelegationGrant.query.get(grant_id)
        if not grant:
            raise ValueError("grant not found")
        return grant.to_dict()

    def list_grants_for_principal(self, principal_id: str) -> List[Dict[str, Any]]:
        rows = DelegationGrant.query.filter_by(principal_id=principal_id).all()
        return [g.to_dict() for g in rows]

    # ------------------------------------------------------------------
    # Validation helpers used by OAuthEngine
    # ------------------------------------------------------------------
    def validate_grant(
        self,
        *,
        grant_id: str,
        delegate_id: str,
        requested_scopes: List[str] | None = None,
    ) -> DelegationGrant:
        grant = DelegationGrant.query.get(grant_id)
        if not grant:
            DelegationAuditLog.log_event(grant_id=None, action="validation_failed", delegate_id=delegate_id, details={"reason": "not_found"})
            raise ValueError("invalid_grant")
        if grant.delegate_id != delegate_id:
            DelegationAuditLog.log_event(grant_id=grant.grant_id, action="validation_failed", delegate_id=delegate_id, details={"reason": "delegate_mismatch"})
            raise ValueError("invalid_grant: delegate mismatch")
        if grant.expires_at < datetime.utcnow():
            DelegationAuditLog.log_event(grant_id=grant.grant_id, action="validation_failed", delegate_id=delegate_id, details={"reason": "expired"})
            raise ValueError("invalid_grant: expired")
        if requested_scopes:
            if not set(requested_scopes).issubset(set(grant.scope)):
                DelegationAuditLog.log_event(grant_id=grant.grant_id, action="validation_failed", delegate_id=delegate_id, details={"reason": "scope_exceeded"})
                raise ValueError("invalid_scope")
        return grant 