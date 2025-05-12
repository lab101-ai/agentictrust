import uuid
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Any

from sqlalchemy import Column, String, DateTime, Integer, Enum, JSON, Index
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from agentictrust.db import Base, db_session
from agentictrust.utils.logger import logger

class DelegationGrant(Base):
    """Represents a delegation approval from a principal (user/agent) to an agent."""
    __tablename__ = 'delegation_grants'

    grant_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    principal_type = Column(Enum('user', 'agent', name='principal_type'), nullable=False)
    principal_id = Column(String(36), nullable=False)
    delegate_id = Column(String(36), nullable=False)  # agent.client_id
    scope = Column(JSON, nullable=False)  # list[str]
    constraints = Column(JSON, nullable=True)
    max_depth = Column(Integer, default=1)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_delegate_expires', 'delegate_id', 'expires_at'),
    )

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------
    @classmethod
    def create(cls, *, principal_type: str, principal_id: str, delegate_id: str, scope: list[str],
               max_depth: int = 1, constraints: dict | None = None, ttl_hours: int = 24) -> "DelegationGrant":
        """Create a new delegation grant.
        
        Args:
            principal_type: Type of the principal ('user' or 'agent')
            principal_id: ID of the principal (user_id or client_id)
            delegate_id: Agent client_id to delegate to
            scope: List of scope IDs being granted
            max_depth: Maximum depth for delegation chain
            constraints: Optional constraints on delegation
            ttl_hours: Time-to-live in hours for the delegation
            
        Returns:
            New DelegationGrant instance
            
        Raises:
            ValueError: If required parameters are missing or invalid
            RuntimeError: For database errors
        """
        # Validate required inputs
        if not principal_type:
            logger.error("Cannot create delegation grant: principal_type is required")
            raise ValueError("principal_type is required")
            
        if principal_type not in ['user', 'agent']:
            logger.error(f"Invalid principal_type: {principal_type}, must be 'user' or 'agent'")
            raise ValueError("principal_type must be 'user' or 'agent'")
            
        if not principal_id:
            logger.error("Cannot create delegation grant: principal_id is required")
            raise ValueError("principal_id is required")
            
        if not delegate_id:
            logger.error("Cannot create delegation grant: delegate_id is required")
            raise ValueError("delegate_id is required")
            
        if not scope or not isinstance(scope, list):
            logger.error(f"Cannot create delegation grant: scope must be a non-empty list, got {type(scope)}")
            raise ValueError("scope must be a non-empty list of scope identifiers")
            
        # Validate max_depth
        if max_depth < 1:
            logger.warning(f"Invalid max_depth: {max_depth}, setting to 1")
            max_depth = 1
            
        try:
            expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
            
            # Create the object
            obj = cls(
                principal_type=principal_type,
                principal_id=principal_id,
                delegate_id=delegate_id,
                scope=scope,
                constraints=constraints or {},
                max_depth=max_depth,
                expires_at=expires_at,
            )
            
            db_session.add(obj)
            db_session.commit()
            
            expiry_time = expires_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            logger.info(f"Created delegation grant from {principal_type} {principal_id} to agent {delegate_id} " 
                       f"with {len(scope)} scopes, expires at {expiry_time} (ID: {obj.grant_id})")
            
            return obj
            
        except IntegrityError as e:
            db_session.rollback()
            err_msg = f"Database integrity error creating delegation grant: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise ValueError(f"Could not create delegation grant due to database constraint: {str(e)}") from e
            
        except SQLAlchemyError as e:
            db_session.rollback()
            err_msg = f"Database error creating delegation grant: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(f"Failed to create delegation grant: {str(e)}") from e
            
        except Exception as e:
            db_session.rollback()
            err_msg = f"Unexpected error creating delegation grant: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(f"Failed to create delegation grant: {str(e)}") from e

    def revoke(self) -> None:
        """Revoke a delegation grant by deleting it.
        
        Raises:
            RuntimeError: For database errors
        """
        try:
            grant_id = self.grant_id
            principal_type = self.principal_type
            principal_id = self.principal_id
            delegate_id = self.delegate_id
            
            db_session.delete(self)
            db_session.commit()
            
            logger.info(f"Revoked delegation grant from {principal_type} {principal_id} to agent {delegate_id} (ID: {grant_id})")
            
        except SQLAlchemyError as e:
            db_session.rollback()
            err_msg = f"Database error revoking delegation grant {self.grant_id}: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(f"Failed to revoke delegation grant: {str(e)}") from e
            
        except Exception as e:
            db_session.rollback()
            err_msg = f"Unexpected error revoking delegation grant {self.grant_id}: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(f"Failed to revoke delegation grant: {str(e)}") from e

    def to_dict(self) -> Dict[str, Any]:
        """Convert delegation grant to dictionary representation.
        
        Returns:
            Dictionary with delegation grant attributes
        """
        try:
            return {
                'grant_id': self.grant_id,
                'principal_type': self.principal_type,
                'principal_id': self.principal_id,
                'delegate_id': self.delegate_id,
                'scope': self.scope,
                'constraints': self.constraints,
                'max_depth': self.max_depth,
                'expires_at': self.expires_at.isoformat() if self.expires_at else None,
                'created_at': self.created_at.isoformat() if self.created_at else None,
            }
        except Exception as e:
            logger.error(f"Error converting delegation grant to dict (ID: {self.grant_id}): {str(e)}")
            # Return a minimal dict with just the ID if there's an error
            return {'grant_id': self.grant_id, 'error': str(e)}
            
    @classmethod
    def get_by_id(cls, grant_id: str) -> "DelegationGrant":
        """Get a delegation grant by ID.
        
        Args:
            grant_id: The grant ID to retrieve
            
        Returns:
            DelegationGrant instance
            
        Raises:
            ValueError: If grant_id is invalid or grant not found
            RuntimeError: For database errors
        """
        if not grant_id:
            logger.error("Cannot get delegation grant: grant_id is None or empty")
            raise ValueError("grant_id is required")
            
        try:
            grant = cls.query.get(grant_id)
            if not grant:
                logger.warning(f"Delegation grant not found with ID: {grant_id}")
                raise ValueError(f"Delegation grant not found with ID: {grant_id}")
                
            logger.debug(f"Retrieved delegation grant: {grant_id}")
            return grant
            
        except SQLAlchemyError as e:
            err_msg = f"Database error retrieving delegation grant with ID {grant_id}: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
            
        except Exception as e:
            if isinstance(e, ValueError) and "not found" in str(e):
                raise  # Re-raise the ValueErrors we generated
                
            err_msg = f"Unexpected error retrieving delegation grant with ID {grant_id}: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
            
    @classmethod
    def list_all(cls) -> List["DelegationGrant"]:
        """List all delegation grants.
        
        Returns:
            List of DelegationGrant instances
            
        Raises:
            RuntimeError: For database errors
        """
        try:
            grants = cls.query.all()
            logger.debug(f"Retrieved {len(grants)} delegation grants")
            return grants
            
        except SQLAlchemyError as e:
            err_msg = f"Database error retrieving all delegation grants: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
            
        except Exception as e:
            err_msg = f"Unexpected error retrieving all delegation grants: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
            
    @classmethod
    def delete_by_id(cls, grant_id: str) -> None:
        """Delete a delegation grant by ID.
        
        Args:
            grant_id: The grant ID to delete
            
        Raises:
            ValueError: If grant_id is invalid or grant not found
            RuntimeError: For database errors
        """
        if not grant_id:
            logger.error("Cannot delete delegation grant: grant_id is None or empty")
            raise ValueError("grant_id is required")
            
        try:
            grant = cls.query.get(grant_id)
            if not grant:
                logger.warning(f"Cannot delete delegation grant: not found with ID {grant_id}")
                raise ValueError(f"Delegation grant not found with ID: {grant_id}")
                
            # Store info for logging after deletion
            principal_type = grant.principal_type
            principal_id = grant.principal_id
            delegate_id = grant.delegate_id
            
            db_session.delete(grant)
            db_session.commit()
            
            logger.info(f"Delegation grant deleted successfully from {principal_type} {principal_id} to agent {delegate_id} (ID: {grant_id})")
            
        except SQLAlchemyError as e:
            db_session.rollback()
            err_msg = f"Database error deleting delegation grant {grant_id}: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
            
        except Exception as e:
            db_session.rollback()
            # Don't wrap ValueError from our own checks
            if isinstance(e, ValueError) and ("not found" in str(e) or "required" in str(e)):
                raise
                
            err_msg = f"Unexpected error deleting delegation grant {grant_id}: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
            
    @classmethod
    def find_by_principal_and_delegate(cls, principal_type: str, principal_id: str, delegate_id: str) -> List["DelegationGrant"]:
        """Find delegation grants by principal and delegate IDs.
        
        Args:
            principal_type: Type of the principal ('user' or 'agent')
            principal_id: ID of the principal (user_id or client_id)
            delegate_id: Agent client_id that was delegated to
            
        Returns:
            List of matching DelegationGrant instances
            
        Raises:
            ValueError: If required parameters are missing or invalid
            RuntimeError: For database errors
        """
        if not principal_type or principal_type not in ['user', 'agent']:
            logger.error(f"Invalid principal_type: {principal_type}, must be 'user' or 'agent'")
            raise ValueError("principal_type must be 'user' or 'agent'")
            
        if not principal_id:
            logger.error("Cannot find delegation grants: principal_id is required")
            raise ValueError("principal_id is required")
            
        if not delegate_id:
            logger.error("Cannot find delegation grants: delegate_id is required")
            raise ValueError("delegate_id is required")
            
        try:
            grants = cls.query.filter_by(
                principal_type=principal_type,
                principal_id=principal_id,
                delegate_id=delegate_id
            ).all()
            
            logger.debug(f"Found {len(grants)} delegation grants from {principal_type} {principal_id} to agent {delegate_id}")
            return grants
            
        except SQLAlchemyError as e:
            err_msg = f"Database error finding delegation grants for {principal_type} {principal_id} to {delegate_id}: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
            
        except Exception as e:
            err_msg = f"Unexpected error finding delegation grants for {principal_type} {principal_id} to {delegate_id}: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
            
    @classmethod
    def find_by_delegate(cls, delegate_id: str, active_only: bool = True) -> List["DelegationGrant"]:
        """Find delegation grants by delegate ID.
        
        Args:
            delegate_id: Agent client_id to find grants for
            active_only: If True, return only non-expired grants
            
        Returns:
            List of matching DelegationGrant instances
            
        Raises:
            ValueError: If delegate_id is missing
            RuntimeError: For database errors
        """
        if not delegate_id:
            logger.error("Cannot find delegation grants: delegate_id is required")
            raise ValueError("delegate_id is required")
            
        try:
            query = cls.query.filter_by(delegate_id=delegate_id)
            
            if active_only:
                now = datetime.utcnow()
                query = query.filter(cls.expires_at > now)
                
            grants = query.all()
            
            if active_only:
                logger.debug(f"Found {len(grants)} active delegation grants for agent {delegate_id}")
            else:
                logger.debug(f"Found {len(grants)} total delegation grants for agent {delegate_id}")
                
            return grants
            
        except SQLAlchemyError as e:
            err_msg = f"Database error finding delegation grants for agent {delegate_id}: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e
            
        except Exception as e:
            err_msg = f"Unexpected error finding delegation grants for agent {delegate_id}: {str(e)}"
            logger.error(f"{err_msg}\nTrace: {traceback.format_exc()}")
            raise RuntimeError(err_msg) from e