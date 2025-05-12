"""
Audit logging for policy evaluation decisions (OPA).
The Policy model has been retired; this log captures policy allow/deny
outcomes returned by OPA for traceability.
"""
from sqlalchemy import Column, String, JSON
from agentictrust.db.models.audit.audit_base import BaseAuditLog
from agentictrust.db import db_session
from agentictrust.utils.logger import logger

class PolicyAuditLog(BaseAuditLog):
    """Audit record for policy decision events."""
    __tablename__ = 'policy_audit_logs'

    client_id = Column(String(36), nullable=False)
    task_id = Column(String(36), nullable=True)
    parent_task_id = Column(String(36), nullable=True)
    decision = Column(String(20), nullable=False)  # allow / deny
    action = Column(String(100), nullable=True)  # action or policy name evaluated
    policy_path = Column(String(200), nullable=True)  # Rego rule path evaluated
    reason = Column(String(200), nullable=True)  # optional human-readable reason
    resource_type = Column(String(50), nullable=True)
    details = Column(JSON, nullable=True)

    @classmethod
    def log(cls, client_id, decision, reason=None, resource_type=None, details=None, task_id=None, parent_task_id=None, policy_path=None, action=None):
        """Create a policy audit record."""
        try:
            # Use policy_path or action (fallback) for the action field
            action_value = action or policy_path
            
            entry = cls(
                client_id=client_id,
                task_id=task_id,
                parent_task_id=parent_task_id,
                action=action_value,  # Use the action column that exists in the DB
                decision=decision,
                reason=reason,
                resource_type=resource_type,
                details=details or {},  # Use details instead of context
            )
            db_session.add(entry)
            db_session.commit()
            return entry
        except Exception as e:
            logger.error(f"Error logging policy audit: {e}")
            db_session.rollback()
            return None

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'client_id': self.client_id,
            'task_id': self.task_id,
            'parent_task_id': self.parent_task_id,
            'decision': self.decision,
            'action': self.action,
            'policy_path': self.policy_path,
            'reason': self.reason,
            'resource_type': self.resource_type,
            'details': self.details or {},
        })
        return data 