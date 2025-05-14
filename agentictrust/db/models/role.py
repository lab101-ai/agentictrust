import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Table, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError
from agentictrust.db import Base, db_session
from agentictrust.utils.logger import logger

role_permissions = Table('role_permissions', Base.metadata,
    Column('role_id', String(36), ForeignKey('roles.role_id'), primary_key=True),
    Column('permission_id', String(36), ForeignKey('permissions.permission_id'), primary_key=True)
)

agent_roles = Table('agent_roles', Base.metadata,
    Column('agent_id', String(36), ForeignKey('agents.client_id'), primary_key=True),
    Column('role_id', String(36), ForeignKey('roles.role_id'), primary_key=True)
)

class Role(Base):
    """Model for agent roles."""
    __tablename__ = 'roles'
    
    role_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    permissions = relationship('Permission', secondary=role_permissions, lazy='subquery', backref='roles')
    agents = relationship('Agent', secondary=agent_roles, lazy='subquery', backref='roles')
    
    @classmethod
    def create(cls, name, description=None):
        """Create a new role."""
        try:
            role = cls(
                name=name,
                description=description
            )
            
            db_session.add(role)
            db_session.commit()
            
            logger.info(f"Created role: {name} (ID: {role.role_id})")
            
            return role
        except SQLAlchemyError as e:
            db_session.rollback()
            logger.error(f"Database error creating role: {str(e)}")
            raise RuntimeError(f"Failed to create role: {str(e)}")
    
    def add_permission(self, permission):
        """Add a permission to this role."""
        if permission not in self.permissions:
            self.permissions.append(permission)
            db_session.commit()
            logger.info(f"Added permission {permission.name} to role {self.name}")
    
    def remove_permission(self, permission):
        """Remove a permission from this role."""
        if permission in self.permissions:
            self.permissions.remove(permission)
            db_session.commit()
            logger.info(f"Removed permission {permission.name} from role {self.name}")
    
    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            'role_id': self.role_id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'permissions': [p.to_dict() for p in self.permissions]
        }
