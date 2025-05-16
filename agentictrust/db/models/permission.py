import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.exc import SQLAlchemyError
from agentictrust.db import Base, db_session
from agentictrust.utils.logger import logger

class Permission(Base):
    """Model for permissions that can be assigned to roles."""
    __tablename__ = 'permissions'
    
    permission_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    resource = Column(String(100), nullable=False)
    action = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    @classmethod
    def create(cls, name, resource, action, description=None):
        """Create a new permission."""
        try:
            permission = cls(
                name=name,
                resource=resource,
                action=action,
                description=description
            )
            
            db_session.add(permission)
            db_session.commit()
            
            logger.info(f"Created permission: {name} (ID: {permission.permission_id})")
            
            return permission
        except SQLAlchemyError as e:
            db_session.rollback()
            logger.error(f"Database error creating permission: {str(e)}")
            raise RuntimeError(f"Failed to create permission: {str(e)}")
    
    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            'permission_id': self.permission_id,
            'name': self.name,
            'description': self.description,
            'resource': self.resource,
            'action': self.action,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
