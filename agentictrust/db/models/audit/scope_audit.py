"""
Audit logging for scope grant and change events.
"""
from sqlalchemy import Column, String, JSON, ForeignKey
from agentictrust.db.models.audit.audit_base import BaseAuditLog
from agentictrust.db import db_session
from agentictrust.utils.logger import logger

class ScopeAuditLog(BaseAuditLog):
    """Model for auditing scope grants and changes."""
    __tablename__ = 'scope_audit_logs'

    scope_id = Column(String(36), ForeignKey('scopes.scope_id'), nullable=False)
    client_id = Column(String(36), ForeignKey('agents.client_id'), nullable=False)
    task_id = Column(String(36), nullable=True)
    parent_task_id = Column(String(36), nullable=True)
    action = Column(String(20), nullable=False)  # granted, revoked, updated
    details = Column(JSON, nullable=True)
    source_ip = Column(String(45), nullable=True)

    @classmethod
    def log(cls, scope_id, client_id, action, task_id=None, parent_task_id=None, details=None, source_ip=None):
        try:
            entry = cls(
                scope_id=scope_id,
                client_id=client_id,
                task_id=task_id,
                parent_task_id=parent_task_id,
                action=action,
                details=details or {},
                source_ip=source_ip
            )
            db_session.add(entry)
            db_session.commit()
            return entry
        except Exception as e:
            logger.error(f"Error creating scope audit log: {str(e)}")
            db_session.rollback()
            return None

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'scope_id': self.scope_id,
            'client_id': self.client_id,
            'task_id': self.task_id,
            'parent_task_id': self.parent_task_id,
            'action': self.action,
            'details': self.details or {},
            'source_ip': self.source_ip,
        })
        return data
