import uuid
from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError
from agentictrust.db import Base, db_session
from agentictrust.utils.logger import logger

class UserAgentAuthorization(Base):
    """Model for tracking which agents a user has authorized."""
    __tablename__ = 'user_agent_authorizations'
    
    authorization_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.user_id'), nullable=False)
    agent_id = Column(String(36), ForeignKey('agents.client_id'), nullable=False)
    scopes = Column(Text, nullable=False)  # Space-separated scope strings
    constraints = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    
    user = relationship('User', backref='agent_authorizations')
    agent = relationship('Agent', backref='user_authorizations')
    
    @classmethod
    def create(cls, user_id, agent_id, scopes, constraints=None, ttl_days=None):
        """Create a new user-agent authorization."""
        try:
            if not user_id:
                logger.error("Cannot create authorization: user_id is required")
                raise ValueError("user_id is required")
                
            if not agent_id:
                logger.error("Cannot create authorization: agent_id is required")
                raise ValueError("agent_id is required")
                
            if not scopes:
                logger.error("Cannot create authorization: scopes is required")
                raise ValueError("scopes is required")
            
            expires_at = None
            if ttl_days:
                expires_at = datetime.utcnow() + timedelta(days=ttl_days)
            
            if isinstance(scopes, list):
                scopes = ' '.join(scopes)
            
            auth = cls(
                user_id=user_id,
                agent_id=agent_id,
                scopes=scopes,
                constraints=constraints or {},
                expires_at=expires_at
            )
            
            db_session.add(auth)
            db_session.commit()
            
            logger.info(f"Created user-agent authorization: {auth.authorization_id} (User: {user_id}, Agent: {agent_id})")
            
            return auth
        except SQLAlchemyError as e:
            db_session.rollback()
            logger.error(f"Database error creating user-agent authorization: {str(e)}")
            raise RuntimeError(f"Failed to create authorization: {str(e)}")
    
    @classmethod
    def get_by_id(cls, authorization_id):
        """Get authorization by ID."""
        auth = cls.query.get(authorization_id)
        if not auth:
            raise ValueError(f"Authorization not found: {authorization_id}")
        return auth
    
    @classmethod
    def get_by_user_and_agent(cls, user_id, agent_id, active_only=True):
        """Get authorization by user and agent IDs."""
        query = cls.query.filter_by(user_id=user_id, agent_id=agent_id)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.first()
    
    @classmethod
    def list_by_user(cls, user_id, active_only=False):
        """List all authorizations for a user."""
        query = cls.query.filter_by(user_id=user_id)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.all()
    
    @classmethod
    def list_by_agent(cls, agent_id, active_only=False):
        """List all authorizations for an agent."""
        query = cls.query.filter_by(agent_id=agent_id)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.all()
    
    def revoke(self):
        """Revoke this authorization."""
        try:
            self.is_active = False
            db_session.commit()
            
            logger.info(f"Revoked user-agent authorization: {self.authorization_id}")
        except SQLAlchemyError as e:
            db_session.rollback()
            logger.error(f"Database error revoking authorization {self.authorization_id}: {str(e)}")
            raise RuntimeError(f"Failed to revoke authorization: {str(e)}")
    
    def update(self, scopes=None, constraints=None, is_active=None, ttl_days=None):
        """Update authorization properties."""
        try:
            if scopes is not None:
                if isinstance(scopes, list):
                    scopes = ' '.join(scopes)
                self.scopes = scopes
                
            if constraints is not None:
                self.constraints = constraints
                
            if is_active is not None:
                self.is_active = is_active
                
            if ttl_days is not None:
                self.expires_at = datetime.utcnow() + timedelta(days=ttl_days)
                
            db_session.commit()
            logger.info(f"Updated user-agent authorization: {self.authorization_id}")
            
            return self
        except SQLAlchemyError as e:
            db_session.rollback()
            logger.error(f"Database error updating authorization {self.authorization_id}: {str(e)}")
            raise RuntimeError(f"Failed to update authorization: {str(e)}")
    
    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            'authorization_id': self.authorization_id,
            'user_id': self.user_id,
            'agent_id': self.agent_id,
            'scopes': self.scopes.split(' ') if isinstance(self.scopes, str) else self.scopes,
            'constraints': self.constraints,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'agent': self.agent.to_dict() if self.agent else None,
        }
