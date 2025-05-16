"""
Audit logging for token issue, refresh, and revoke events.
"""
from sqlalchemy import Column, String, JSON, ForeignKey
from agentictrust.db.models.audit.audit_base import BaseAuditLog
from agentictrust.db import db_session
from agentictrust.utils.logger import logger

class TokenAuditLog(BaseAuditLog):
    """Model for auditing token issue, refresh, and revoke events."""
    __tablename__ = 'token_audit_logs'

    token_id = Column(String(36), ForeignKey('issued_tokens.token_id'), nullable=False)
    client_id = Column(String(36), ForeignKey('agents.client_id'), nullable=False)
    task_id = Column(String(36), nullable=True)
    parent_task_id = Column(String(36), nullable=True)
    event_type = Column(String(20), nullable=False)  # issued, refreshed, revoked
    details = Column(JSON, nullable=True)
    source_ip = Column(String(45), nullable=True)

    # Delegation context (added Task 5)
    delegator_sub = Column(String(255), nullable=True)
    delegation_chain = Column(JSON, nullable=True)  # list[str]

    @classmethod
    def log(
        cls,
        token_id,
        client_id,
        event_type,
        task_id: str | None = None,
        parent_task_id: str | None = None,
        details: dict | None = None,
        source_ip: str | None = None,
        *,
        delegator_sub: str | None = None,
        delegation_chain: list[str] | None = None,
    ):
        try:
            entry = cls(
                token_id=token_id,
                client_id=client_id,
                task_id=task_id,
                parent_task_id=parent_task_id,
                event_type=event_type,
                details=details or {},
                source_ip=source_ip,
                delegator_sub=delegator_sub,
                delegation_chain=delegation_chain or [],
            )
            db_session.add(entry)
            db_session.commit()
            return entry
        except Exception as e:
            logger.error(f"Error creating token audit log: {str(e)}")
            db_session.rollback()
            return None

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'token_id': self.token_id,
            'client_id': self.client_id,
            'task_id': self.task_id,
            'parent_task_id': self.parent_task_id,
            'event_type': self.event_type,
            'details': self.details or {},
            'source_ip': self.source_ip,
            'delegator_sub': self.delegator_sub,
            'delegation_chain': self.delegation_chain or [],
        })
        return data
