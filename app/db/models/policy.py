import uuid
from datetime import datetime
import json
import re
import logging
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.db import Base, db_session
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

# Association table for policy-scopes many-to-many relationship
policy_scopes = Table(
    'policy_scopes',
    Base.metadata,
    Column('policy_id', String(36), ForeignKey('policies.policy_id'), primary_key=True),
    Column('scope_id', String(36), ForeignKey('scopes.scope_id'), primary_key=True)
)

class Policy(Base):
    """Model for ABAC policies that define conditional access rules."""
    __tablename__ = 'policies'
    
    policy_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    effect = Column(String(10), default="allow")  # allow or deny
    conditions = Column(Text, nullable=False)  # JSON string of condition rules
    # Remove scope_id column and replace with many-to-many relationship
    priority = Column(Integer, default=10)  # Higher priority policies are evaluated first
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Define relationship with scopes
    scopes = relationship("Scope", secondary=policy_scopes, backref="policies")
    
    @classmethod
    def create(cls, name, conditions, effect="allow", description=None, scope_ids=None, priority=10):
        """Create a new ABAC policy."""
        import traceback
        from app.db.models.scope import Scope
        
        if not name:
            logger.error("Cannot create policy: name is required")
            raise ValueError("Policy name is required")
        
        # Validate effect value
        if effect not in ["allow", "deny"]:
            logger.warning(f"Creating policy with non-standard effect value: {effect}")
            
        # Validate conditions format - it should be a valid JSON string or dict
        try:
            if isinstance(conditions, dict):
                conditions_json = json.dumps(conditions)
            else:
                # Validate JSON format
                json.loads(conditions)
                conditions_json = conditions
        except json.JSONDecodeError as e:
            err_msg = f"Invalid conditions format: {str(e)}"
            logger.error(f"{err_msg}\nProvided conditions: {conditions}")
            raise ValueError("Conditions must be a valid JSON string or dictionary") from e
        except Exception as e:
            err_msg = f"Unexpected error validating conditions: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise ValueError("Error processing policy conditions") from e
        
        # Create policy object
        policy = cls(
            name=name,
            description=description,
            effect=effect,
            conditions=conditions_json,
            priority=priority
        )
        
        # Track invalid scope IDs for logging
        invalid_scope_ids = []
        
        # Add scopes to the policy if provided
        if scope_ids:
            for scope_id in scope_ids:
                try:
                    scope = Scope.query.get(scope_id)
                    if scope:
                        policy.scopes.append(scope)
                        logger.debug(f"Added scope '{scope.name}' ({scope_id}) to policy '{name}'")
                    else:
                        invalid_scope_ids.append(scope_id)
                except SQLAlchemyError as e:
                    logger.warning(f"Error retrieving scope {scope_id} for policy {name}: {str(e)}")
                    invalid_scope_ids.append(scope_id)
            
            if invalid_scope_ids:
                logger.warning(f"The following scope IDs were not found: {', '.join(invalid_scope_ids)}")
        
        try:
            db_session.add(policy)
            db_session.commit()
            logger.info(f"Created policy '{name}' (ID: {policy.policy_id}) with {len(policy.scopes)} scopes")
            return policy
        except SQLAlchemyError as e:
            db_session.rollback()
            err_msg = f"Database error creating policy '{name}': {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            
            # Check for common errors
            if 'unique constraint' in str(e).lower():
                raise ValueError(f"A policy with the name '{name}' already exists") from e
            raise RuntimeError(f"Failed to create policy: {str(e)}") from e
        except Exception as e:
            db_session.rollback()
            err_msg = f"Unexpected error creating policy '{name}': {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(f"Failed to create policy: {str(e)}") from e
    
    def update(self, **kwargs):
        """Update policy attributes."""
        import traceback
        from app.db.models.scope import Scope
        
        if not kwargs:
            logger.warning(f"No update data provided for policy {self.policy_id} ({self.name})")
            return self
            
        properties_updated = []
        
        # Validate and process conditions if provided
        if 'conditions' in kwargs:
            try:
                if isinstance(kwargs['conditions'], dict):
                    kwargs['conditions'] = json.dumps(kwargs['conditions'])
                else:
                    # Validate JSON format
                    json.loads(kwargs['conditions'])
                properties_updated.append('conditions')
            except json.JSONDecodeError as e:
                err_msg = f"Invalid conditions format: {str(e)}"
                logger.error(f"{err_msg}\nProvided conditions: {kwargs['conditions']}")
                raise ValueError("Conditions must be a valid JSON string or dictionary") from e
        
        # Validate effect if provided
        if 'effect' in kwargs:
            if kwargs['effect'] not in ["allow", "deny"]:
                logger.warning(f"Updating policy with non-standard effect value: {kwargs['effect']}")
            properties_updated.append(f"effect: '{kwargs['effect']}'")
        
        # Handle scope_ids separately
        scope_ids = kwargs.pop('scope_ids', None)
        invalid_scope_ids = []
        
        if scope_ids is not None:
            original_scope_count = len(self.scopes) if self.scopes else 0
            
            # Clear existing scopes
            self.scopes = []
            properties_updated.append('scopes')
            
            # Add new scopes
            for scope_id in scope_ids:
                try:
                    scope = Scope.query.get(scope_id)
                    if scope:
                        self.scopes.append(scope)
                        logger.debug(f"Added scope '{scope.name}' ({scope_id}) to policy '{self.name}'")
                    else:
                        invalid_scope_ids.append(scope_id)
                except SQLAlchemyError as e:
                    logger.warning(f"Error retrieving scope {scope_id} for policy {self.name}: {str(e)}")
                    invalid_scope_ids.append(scope_id)
            
            if invalid_scope_ids:
                logger.warning(f"Policy update: The following scope IDs were not found: {', '.join(invalid_scope_ids)}")
                
            logger.info(f"Updated scopes for policy '{self.name}' from {original_scope_count} to {len(self.scopes)}")
        
        # Update other attributes
        for key, value in kwargs.items():
            if hasattr(self, key) and key not in ['conditions', 'scope_ids', 'scopes']:
                old_value = getattr(self, key)
                setattr(self, key, value)
                
                # Add to properties updated list with specific formatting
                if key == 'name':
                    properties_updated.append(f"{key}: '{old_value}' -> '{value}'")
                elif key == 'priority':
                    properties_updated.append(f"{key}: {old_value} -> {value}")
                elif key == 'is_active' and isinstance(value, bool):
                    properties_updated.append(f"{key}: {old_value} -> {value}")
                elif key not in properties_updated:
                    properties_updated.append(key)
        
        if not properties_updated:
            logger.warning(f"No valid properties to update for policy {self.policy_id}")
            return self
            
        self.updated_at = datetime.utcnow()
        try:
            db_session.commit()
            logger.info(f"Updated policy {self.policy_id} ({self.name}) properties: {', '.join(properties_updated)}")
        except IntegrityError as e:
            db_session.rollback()
            err_msg = f"Database integrity error updating policy {self.policy_id}: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            if 'unique constraint' in str(e).lower() and 'name' in kwargs:
                raise ValueError(f"A policy with name '{kwargs['name']}' already exists") from e
            raise ValueError(f"Could not update policy due to database constraint: {str(e)}") from e
        except SQLAlchemyError as e:
            db_session.rollback()
            err_msg = f"Database error updating policy {self.policy_id}: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
        except Exception as e:
            db_session.rollback()
            err_msg = f"Unexpected error updating policy {self.policy_id}: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
        
        return self
    
    def to_dict(self):
        """Convert policy to dictionary representation."""
        return {
            'policy_id': self.policy_id,
            'name': self.name,
            'description': self.description,
            'effect': self.effect,
            'conditions': json.loads(self.conditions),
            'scopes': [scope.scope_id for scope in self.scopes] if self.scopes else [],
            'priority': self.priority,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
    @classmethod
    def get_by_id(cls, policy_id):
        """Get policy by ID."""
        import traceback
        
        if not policy_id:
            logger.error("Cannot get policy: policy_id is None or empty")
            raise ValueError("policy_id is required")
            
        try:
            policy = cls.query.get(policy_id)
            if not policy:
                logger.warning(f"Policy not found with ID: {policy_id}")
                raise ValueError(f"Policy not found with ID: {policy_id}")
            logger.debug(f"Retrieved policy: {policy_id} - {policy.name}")
            return policy
        except SQLAlchemyError as e:
            err_msg = f"Database error retrieving policy with ID {policy_id}: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
        except Exception as e:
            if isinstance(e, ValueError) and "Policy not found" in str(e):
                raise  # Re-raise the ValueErrors we generated
            err_msg = f"Unexpected error retrieving policy with ID {policy_id}: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
    
    @classmethod
    def find_by_name(cls, name):
        """Find a policy by name."""
        import traceback
        
        if not name:
            logger.warning("Cannot find policy: name is None or empty")
            return None
            
        try:
            policy = cls.query.filter_by(name=name).first()
            if policy:
                logger.debug(f"Found policy by name: {name} (ID: {policy.policy_id})")
            else:
                logger.debug(f"No policy found with name: {name}")
            return policy
        except SQLAlchemyError as e:
            err_msg = f"Database error finding policy by name '{name}': {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
        except Exception as e:
            err_msg = f"Unexpected error finding policy by name '{name}': {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
        
    @classmethod
    def list_all(cls):
        """List all policies."""
        import traceback
        
        try:
            policies = cls.query.all()
            logger.debug(f"Retrieved {len(policies)} policies")
            return policies
        except SQLAlchemyError as e:
            err_msg = f"Database error retrieving all policies: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
        except Exception as e:
            err_msg = f"Unexpected error retrieving all policies: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
        
    @classmethod
    def delete_by_id(cls, policy_id):
        """Delete a policy by ID."""
        import traceback
        
        if not policy_id:
            logger.error("Cannot delete policy: policy_id is None or empty")
            raise ValueError("policy_id is required")
            
        try:
            policy = cls.query.get(policy_id)
            if not policy:
                logger.warning(f"Cannot delete policy: not found with ID {policy_id}")
                raise ValueError(f"Policy not found with ID: {policy_id}")
            
            # Store name for logging after deletion
            policy_name = policy.name
            
            # Before deleting, check if policy is referenced by anything
            # (This would need custom checks appropriate to your application)
            # Example: check if policy is used by any agents, etc.
            
            db_session.delete(policy)
            db_session.commit()
            logger.info(f"Policy deleted successfully: {policy_id} - {policy_name}")
        except IntegrityError as e:
            db_session.rollback()
            err_msg = f"Cannot delete policy {policy_id} due to integrity constraints: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise ValueError(f"Cannot delete policy due to existing relationships: {str(e)}") from e
        except SQLAlchemyError as e:
            db_session.rollback()
            err_msg = f"Database error deleting policy {policy_id}: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
        except Exception as e:
            db_session.rollback()
            # Don't wrap ValueError from our own checks
            if isinstance(e, ValueError) and ("not found" in str(e) or "required" in str(e)):
                raise
            err_msg = f"Unexpected error deleting policy {policy_id}: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
