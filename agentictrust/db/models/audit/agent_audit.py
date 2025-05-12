"""
Audit logging for agent create/update/delete events.
"""
from sqlalchemy import Column, String, JSON, ForeignKey
from agentictrust.db.models.audit.audit_base import BaseAuditLog
from agentictrust.db import db_session
from agentictrust.utils.logger import logger

class AgentAuditLog(BaseAuditLog):
    """Model for auditing agent create/update/delete events."""
    __tablename__ = 'agent_audit_logs'

    agent_id = Column(String(36), ForeignKey('agents.client_id'), nullable=False)
    action = Column(String(20), nullable=False)  # created, updated, deleted
    details = Column(JSON, nullable=True)
    source_ip = Column(String(45), nullable=True)

    @classmethod
    def log(cls, agent_id, action, details=None, source_ip=None):
        try:
            entry = cls(agent_id=agent_id, action=action, details=details or {}, source_ip=source_ip)
            db_session.add(entry)
            db_session.commit()
            return entry
        except Exception as e:
            logger.error(f"Error creating agent audit log: {str(e)}")
            db_session.rollback()
            return None

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'agent_id': self.agent_id,
            'action': self.action,
            'details': self.details or {},
            'source_ip': self.source_ip,
        })
        return data
