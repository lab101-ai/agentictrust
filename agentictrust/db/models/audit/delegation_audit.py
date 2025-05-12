from sqlalchemy import Column, String, ForeignKey, JSON
from agentictrust.db.models.audit.audit_base import BaseAuditLog
from agentictrust.db import db_session
from agentictrust.utils.logger import logger

class DelegationAuditLog(BaseAuditLog):
    """Audit log rows for delegation-grant lifecycle and delegated token issuance."""
    __tablename__ = 'delegation_audit_logs'

    grant_id = Column(String(36), ForeignKey('delegation_grants.grant_id'), nullable=True)
    principal_id = Column(String(36), nullable=True)
    delegate_id = Column(String(36), nullable=True)
    token_id = Column(String(36), nullable=True, index=True)
    action = Column(String(50), nullable=False)  # created | revoked | token_issued | validation_failed
    scope = Column(JSON, nullable=True)
    details = Column(JSON, nullable=True)

    @classmethod
    def log_event(cls, *, grant_id: str | None, action: str, principal_id: str | None = None,
                  delegate_id: str | None = None, token_id: str | None = None,
                  scope: list[str] | None = None, details: dict | None = None):
        try:
            row = cls(
                grant_id=grant_id,
                principal_id=principal_id,
                delegate_id=delegate_id,
                token_id=token_id,
                action=action,
                scope=scope or [],
                details=details or {},
            )
            db_session.add(row)
            db_session.commit()
            return row
        except Exception as e:
            logger.error(f"Failed to insert DelegationAuditLog: {e}")
            db_session.rollback()
            return None

    def to_dict(self):
        base = super().to_dict()
        base.update({
            'grant_id': self.grant_id,
            'principal_id': self.principal_id,
            'delegate_id': self.delegate_id,
            'token_id': self.token_id,
            'action': self.action,
            'scope': self.scope,
            'details': self.details or {},
        })
        return base 