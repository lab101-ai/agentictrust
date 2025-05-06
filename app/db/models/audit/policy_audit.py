"""
Policy-related audit logging models.
"""
import logging
from sqlalchemy import Column, String, ForeignKey, JSON
from app.db.models.audit.audit_base import BaseAuditLog
from app.db import db_session
logger = logging.getLogger(__name__)

class PolicyAuditLog(BaseAuditLog):
    """Model for auditing policy evaluations and access decisions."""
    __tablename__ = 'policy_audit_logs'
    
    # Agent context (who is requesting access)
    client_id = Column(String(36), ForeignKey('agents.client_id'), nullable=True)
    # Task context for linking policy decisions to specific tasks
    task_id = Column(String(36), nullable=True)
    parent_task_id = Column(String(36), nullable=True)
    
    # Optional token context
    token_id = Column(String(36), nullable=True, index=True)
    
    # Policy context
    policy_id = Column(String(36), ForeignKey('policies.policy_id'), nullable=True)
    
    # Event details
    action = Column(String(50), nullable=False)  # Type of action being evaluated (read, write, etc.)
    resource_type = Column(String(50), nullable=True)  # Type of resource being accessed
    resource_id = Column(String(100), nullable=True)  # Identifier for the resource
    decision = Column(String(20), nullable=False)  # allowed, denied
    reason = Column(String(200), nullable=True)  # Why the decision was made
    source_ip = Column(String(45), nullable=True)
    
    # Additional context as JSON
    context = Column(JSON, nullable=True)
    
    @classmethod
    def log(cls, client_id, action, decision, 
                          policy_id=None, token_id=None, task_id=None, parent_task_id=None,
                          resource_type=None, resource_id=None, reason=None, source_ip=None, context=None):
        """Log a policy decision event."""
        try:
            log_entry = cls(
                client_id=client_id,
                token_id=token_id,
                task_id=task_id,
                parent_task_id=parent_task_id,
                policy_id=policy_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                decision=decision,
                reason=reason,
                source_ip=source_ip,
                context=context or {}
            )
            
            db_session.add(log_entry)
            db_session.commit()
            return log_entry
        except Exception as e:
            logger.error(f"Error creating policy audit log: {str(e)}")
            db_session.rollback()
            return None

    def to_dict(self):
        """Convert the policy audit log to a dictionary including task context."""
        return {
            'log_id': self.log_id,
            'client_id': self.client_id,
            'token_id': self.token_id,
            'policy_id': self.policy_id,
            'task_id': self.task_id,
            'parent_task_id': self.parent_task_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'decision': self.decision,
            'reason': self.reason,
            'source_ip': self.source_ip,
            'context': self.context or {}
        }
