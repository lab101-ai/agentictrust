import uuid
import traceback
import logging
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text, Table, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.db import Base, db_session

logger = logging.getLogger(__name__)

class Scope(Base):
    """Model for OAuth scopes that can be assigned to tokens."""
    __tablename__ = 'scopes'
    
    scope_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)  # Read, Write, Admin, Tool
    is_sensitive = Column(Boolean, default=False)
    requires_approval = Column(Boolean, default=False)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def create(cls, name, description=None, category="read", is_sensitive=False, 
               requires_approval=False, is_default=False):
        """Create a new OAuth scope."""
        if not name:
            logger.error("Cannot create scope: name is required")
            raise ValueError("Scope name is required")
            
        if not category:
            logger.error("Cannot create scope: category is required")
            raise ValueError("Scope category is required")
            
        # Validate category is one of the expected values
        valid_categories = ["read", "write", "admin", "tool"]
        if category not in valid_categories:
            logger.warning(f"Creating scope with non-standard category: {category}")
            
        # Create scope instance
        scope = cls(
            name=name,
            description=description,
            category=category,
            is_sensitive=is_sensitive,
            requires_approval=requires_approval,
            is_default=is_default
        )
        
        # Add to database with detailed error handling
        try:
            db_session.add(scope)
            db_session.commit()
            logger.info(f"Scope '{name}' created successfully with ID: {scope.scope_id}, category: {category}")
            
            # Log additional information about sensitive or approval-required scopes
            if is_sensitive:
                logger.info(f"Created sensitive scope: {name} (ID: {scope.scope_id})")
            if requires_approval:
                logger.info(f"Created approval-required scope: {name} (ID: {scope.scope_id})")
            if is_default:
                logger.info(f"Created default scope: {name} (ID: {scope.scope_id})")
                
        except IntegrityError as e:
            db_session.rollback()
            logger.error(f"Database integrity error creating scope '{name}': {str(e)}")
            if 'unique constraint' in str(e).lower():
                raise ValueError(f"A scope with name '{name}' already exists") from e
            raise ValueError(f"Could not create scope due to database constraint: {str(e)}") from e
        except SQLAlchemyError as e:
            db_session.rollback()
            err_msg = f"Database error creating scope '{name}': {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
        except Exception as e:
            db_session.rollback()
            err_msg = f"Unexpected error creating scope '{name}': {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
        
        return scope
    
    def update(self, **kwargs):
        """Update scope attributes."""
        if not kwargs:
            logger.warning(f"No update data provided for scope {self.scope_id} ({self.name})")
            return self
            
        properties_updated = []
        
        # Validate category if provided
        if 'category' in kwargs:
            valid_categories = ["read", "write", "admin", "tool"]
            if kwargs['category'] not in valid_categories:
                logger.warning(f"Updating scope with non-standard category: {kwargs['category']}")
        
        # Update attributes with logging for each field
        for key, value in kwargs.items():
            if hasattr(self, key):
                old_value = getattr(self, key)
                setattr(self, key, value)
                
                # Log the specific field being updated
                if isinstance(old_value, bool) and isinstance(value, bool):
                    properties_updated.append(f"{key}: {old_value} -> {value}")
                elif key == 'name':
                    properties_updated.append(f"{key}: '{old_value}' -> '{value}'")
                else:
                    properties_updated.append(key)
        
        if not properties_updated:
            logger.warning(f"No valid properties to update for scope {self.scope_id}")
            return self
            
        self.updated_at = datetime.utcnow()
        try:
            db_session.commit()
            logger.info(f"Updated scope {self.scope_id} ({self.name}) properties: {', '.join(properties_updated)}")
        except IntegrityError as e:
            db_session.rollback()
            logger.error(f"Database integrity error updating scope {self.scope_id}: {str(e)}")
            if 'unique constraint' in str(e).lower() and 'name' in kwargs:
                raise ValueError(f"A scope with name '{kwargs['name']}' already exists") from e
            raise ValueError(f"Could not update scope due to database constraint: {str(e)}") from e
        except SQLAlchemyError as e:
            db_session.rollback()
            err_msg = f"Database error updating scope {self.scope_id}: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
        except Exception as e:
            db_session.rollback()
            err_msg = f"Unexpected error updating scope {self.scope_id}: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
            
        return self
    
    def to_dict(self):
        """Convert scope to dictionary representation."""
        return {
            'scope_id': self.scope_id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'is_sensitive': self.is_sensitive,
            'requires_approval': self.requires_approval,
            'is_default': self.is_default,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
    @classmethod
    def get_by_id(cls, scope_id):
        """Get scope by ID."""
        if not scope_id:
            logger.error("Cannot get scope: scope_id is None or empty")
            raise ValueError("scope_id is required")
            
        try:
            scope = cls.query.get(scope_id)
            if not scope:
                logger.warning(f"Scope not found with ID: {scope_id}")
                raise ValueError(f"Scope not found with ID: {scope_id}")
            logger.debug(f"Retrieved scope: {scope_id} - {scope.name}")
            return scope
        except SQLAlchemyError as e:
            err_msg = f"Database error retrieving scope with ID {scope_id}: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
        
    @classmethod
    def list_all(cls):
        """List all scopes."""
        try:
            scopes = cls.query.all()
            logger.debug(f"Retrieved {len(scopes)} scopes")
            return scopes
        except SQLAlchemyError as e:
            err_msg = f"Database error retrieving all scopes: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
        
    @classmethod
    def delete_by_id(cls, scope_id):
        """Delete a scope by ID."""
        if not scope_id:
            logger.error("Cannot delete scope: scope_id is None or empty")
            raise ValueError("scope_id is required")
            
        try:
            scope = cls.query.get(scope_id)
            if not scope:
                logger.warning(f"Cannot delete scope: not found with ID {scope_id}")
                raise ValueError(f"Scope not found with ID: {scope_id}")
                
            # Check if scope is associated with any users, tools, or policies before deletion
            if hasattr(scope, 'users') and scope.users and len(scope.users) > 0:
                msg = f"Cannot delete scope {scope_id} ({scope.name}) as it is associated with {len(scope.users)} users"
                logger.warning(msg)
                raise ValueError(msg)
                
            if hasattr(scope, 'policies') and scope.policies and len(scope.policies) > 0:
                msg = f"Cannot delete scope {scope_id} ({scope.name}) as it is associated with {len(scope.policies)} policies"
                logger.warning(msg)
                raise ValueError(msg)
                
            scope_name = scope.name  # Store for logging after deletion
            db_session.delete(scope)
            db_session.commit()
            logger.info(f"Scope deleted successfully: {scope_id} - {scope_name}")
        except IntegrityError as e:
            db_session.rollback()
            err_msg = f"Cannot delete scope {scope_id} due to integrity constraints: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise ValueError(f"Cannot delete scope due to existing relationships: {str(e)}") from e
        except SQLAlchemyError as e:
            db_session.rollback()
            err_msg = f"Database error deleting scope {scope_id}: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
        except Exception as e:
            db_session.rollback()
            err_msg = f"Unexpected error deleting scope {scope_id}: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
            
    @classmethod
    def find_by_name(cls, name):
        """Find a scope by name."""
        if not name:
            logger.warning("Cannot find scope: name is None or empty")
            return None
            
        try:
            scope = cls.query.filter_by(name=name).first()
            if scope:
                logger.debug(f"Found scope by name: {name} (ID: {scope.scope_id})")
            else:
                logger.debug(f"No scope found with name: {name}")
            return scope
        except SQLAlchemyError as e:
            err_msg = f"Database error finding scope by name '{name}': {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e

# Association table for agent-default scopes many-to-many relationship
agent_default_scopes = Table(
    'agent_default_scopes',
    Base.metadata,
    Column('agent_id', String(36), ForeignKey('agents.client_id'), primary_key=True),
    Column('scope_id', String(36), ForeignKey('scopes.scope_id'), primary_key=True)
)

# Association table for tool-required scopes many-to-many relationship
tool_required_scopes = Table(
    'tool_required_scopes',
    Base.metadata,
    Column('tool_id', String(36), ForeignKey('tools.tool_id'), primary_key=True),
    Column('scope_id', String(36), ForeignKey('scopes.scope_id'), primary_key=True)
)
