"""
Audit logging for resource CRUD events.
"""
import logging
from sqlalchemy import Column, String, JSON, ForeignKey
from app.db.models.audit.audit_base import BaseAuditLog
from app.db import db_session

logger = logging.getLogger(__name__)

class ResourceAuditLog(BaseAuditLog):
    """Model for auditing resource CRUD events."""
    __tablename__ = 'resource_audit_logs'

    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(100), nullable=True)
    action = Column(String(20), nullable=False)  # created, updated, deleted, read
    details = Column(JSON, nullable=True)
    source_ip = Column(String(45), nullable=True)

    @classmethod
    def log(cls, resource_type, resource_id, action, details=None, source_ip=None):
        try:
            entry = cls(
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
                details=details or {},
                source_ip=source_ip
            )
            db_session.add(entry)
            db_session.commit()
            return entry
        except Exception as e:
            logger.error(f"Error creating resource audit log: {str(e)}")
            db_session.rollback()
            return None

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'action': self.action,
            'details': self.details or {},
            'source_ip': self.source_ip,
        })
        return data
