"""Core user management logic."""
from typing import Dict, Any, List, Optional
import uuid
from agentictrust.db.models import User, Scope
from agentictrust.db import db_session
from agentictrust.utils.logger import logger

class UserEngine:
    """Core engine for managing user lifecycle."""
    def __init__(self):
        # No internal state needed for now
        pass

    def create_user(self, username: str, email: str, full_name: Optional[str] = None,
                    hashed_password: Optional[str] = None, is_external: bool = False,
                    department: Optional[str] = None, job_title: Optional[str] = None,
                    level: Optional[str] = None, scopes: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a new user and return dict."""
        # Basic validation
        if not username or not email:
            raise ValueError("Username and email are required")
            
        # Process scope and policy identifiers
        scope_ids: List[str] = []
        
        # Process scopes
        for s in scopes or []:
            if len(s) == 36 and "-" in s:  # Already a UUID
                scope_ids.append(s)
            else:  # A scope name
                scope_obj = Scope.find_by_name(s)
                if scope_obj:
                    scope_ids.append(scope_obj.scope_id)
                else:
                    raise ValueError(f"Scope '{s}' not found")
                    
        # Create the user via the User model
        user = User.create(
            username=username, email=email, full_name=full_name,
            hashed_password=hashed_password, is_external=is_external,
            department=department, job_title=job_title, level=level,
            scope_ids=scope_ids
        )
        return user.to_dict()

    def list_users(self) -> List[Dict[str, Any]]:
        """List all users"""
        return [user.to_dict() for user in User.list_all()]

    def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get user by ID"""
        user = User.get_by_id(user_id)
        return user.to_dict()

    def update_user(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a user and return dict"""
        user = User.get_by_id(user_id)
        user.update(**data)
        return user.to_dict()

    def delete_user(self, user_id: str) -> None:
        """Delete a user by ID"""
        User.delete_by_id(user_id)
        
    def find_user_by_auth0_id(self, auth0_id):
        """Find user by Auth0 ID."""
        try:
            user = User.query.filter_by(auth0_id=auth0_id).first()
            return user
        except Exception as e:
            logger.error(f"Error finding user by Auth0 ID: {str(e)}")
            raise RuntimeError(f"Database error finding user: {str(e)}")

    def create_user_from_auth0(self, data):
        """Create user from Auth0 user data."""
        try:
            username = data.email.split('@')[0]
            if User.query.filter_by(username=username).first():
                username = f"{username}_{uuid.uuid4().hex[:8]}"
            
            user = User(
                username=username,
                email=data.email,
                full_name=data.full_name,
                auth0_id=data.auth0_id,
                is_external=True,
                social_provider='auth0',
                social_provider_id=data.auth0_id,
            )
            
            if data.auth0_metadata:
                user.set_auth0_metadata(data.auth0_metadata)
            
            db_session.add(user)
            db_session.commit()
            
            logger.info(f"Created new user from Auth0: {user.user_id} (Auth0 ID: {data.auth0_id})")
            
            return user
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error creating user from Auth0: {str(e)}")
            raise RuntimeError(f"Failed to create user: {str(e)}")
