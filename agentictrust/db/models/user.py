import uuid
import json
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Table, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from agentictrust.db import Base, db_session
from agentictrust.utils.logger import logger

# Association table for user-scope many-to-many relationship (policies now live in OPA only)
user_scopes = Table(
    'user_scopes',
    Base.metadata,
    Column('user_id', String(36), ForeignKey('users.user_id'), primary_key=True),
    Column('scope_id', String(36), ForeignKey('scopes.scope_id'), primary_key=True)
)

class User(Base):
    """Model for users who can initiate agents and have assigned scopes/policies."""
    __tablename__ = 'users'

    user_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    full_name = Column(String(200), nullable=True)
    hashed_password = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)
    is_external = Column(Boolean, default=False)
    # New organizational attributes
    department = Column(String(100), nullable=True)
    job_title = Column(String(100), nullable=True)
    level = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Arbitrary user metadata (e.g., partner affiliation)
    attributes = Column(JSON, nullable=True)
    
    auth0_id = Column(String(100), nullable=True, unique=True)
    auth0_metadata = Column(Text, nullable=True)  # JSON field to store Auth0 user metadata
    social_provider = Column(String(50), nullable=True)  # e.g., 'google', 'github'
    social_provider_id = Column(String(100), nullable=True)
    last_login = Column(DateTime, nullable=True)
    refresh_token = Column(String(512), nullable=True)

    scopes = relationship('Scope', secondary=user_scopes, backref='users')
    
    def set_auth0_metadata(self, metadata):
        """Set Auth0 metadata as JSON string."""
        if metadata and isinstance(metadata, dict):
            self.auth0_metadata = json.dumps(metadata)
    
    def get_auth0_metadata(self):
        """Get Auth0 metadata as dictionary."""
        if self.auth0_metadata:
            try:
                return json.loads(self.auth0_metadata)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in auth0_metadata for user {self.user_id}")
        return {}
    
    @classmethod
    def create(cls, username, email, full_name=None, hashed_password=None, is_external=False, department=None, job_title=None, level=None, attributes=None, scope_ids=None):
        """Create a new user."""
        # Check uniqueness of username and email
        if cls.query.filter_by(username=username).first():
            raise ValueError("Username already exists")
        if cls.query.filter_by(email=email).first():
            raise ValueError("Email already exists")
            
        user = cls(
            username=username,
            email=email,
            full_name=full_name,
            hashed_password=hashed_password,
            is_external=is_external,
            department=department,
            job_title=job_title,
            level=level,
            attributes=attributes or {}
        )
        if scope_ids:
            from agentictrust.db.models.scope import Scope
            for scope_id in scope_ids:
                scope = Scope.query.get(scope_id)
                if scope:
                    user.scopes.append(scope)
        try:
            db_session.add(user)
            db_session.commit()
            logger.debug(f"Created user {user.user_id} with username {username}")
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            db_session.rollback()
            raise
        return user

    def update(self, **kwargs):
        """Update user attributes."""
        scope_ids = kwargs.pop('scope_ids', None)
        if scope_ids is not None:
            self.scopes = []
            from agentictrust.db.models.scope import Scope
            for scope_id in scope_ids:
                scope = Scope.query.get(scope_id)
                if scope:
                    self.scopes.append(scope)
        # Handle attributes merge
        attrs_update = kwargs.pop('attributes', None)
        if attrs_update is not None:
            self.attributes = {**(self.attributes or {}), **attrs_update}
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
        try:
            db_session.commit()
            logger.debug(f"Updated user {self.user_id}")
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            db_session.rollback()
            raise
        return self

    def to_dict(self):
        """Convert user to dict."""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'is_external': self.is_external,
            'department': self.department,
            'job_title': self.job_title,
            'level': self.level,
            'attributes': self.attributes or {},
            'scopes': [scope.scope_id for scope in self.scopes],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'auth0_id': self.auth0_id,
            'social_provider': self.social_provider,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'auth0_metadata': self.get_auth0_metadata()
        }

    @classmethod
    def get_by_id(cls, user_id):
        """Get user by ID."""
        user = cls.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        return user

    @classmethod
    def list_all(cls):
        """List all users."""
        return cls.query.all()
        
    @classmethod
    def delete_by_id(cls, user_id):
        """Delete a user by ID."""
        user = cls.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        try:
            db_session.delete(user)
            db_session.commit()
            logger.debug(f"Deleted user {user_id}")
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            db_session.rollback()
            raise
