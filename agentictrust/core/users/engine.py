"""Core user management logic."""
from typing import Dict, Any, List, Optional
from agentictrust.db.models import User, Scope
from agentictrust.utils.logger import logger
from agentictrust.utils.auth import hash_password, create_access_token
from agentictrust.db import db_session

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
                    
        # Hash password if needed
        if hashed_password is None:
            raise ValueError("Password is required")
        if not hashed_password.startswith("pbkdf2:"):
            hashed_password = hash_password(hashed_password)

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
        # Re-hash password if it is being updated and looks unhashed
        if "hashed_password" in data and data["hashed_password"]:
            if not data["hashed_password"].startswith("pbkdf2:"):
                data["hashed_password"] = hash_password(data["hashed_password"])
        user.update(**data)
        return user.to_dict()

    def delete_user(self, user_id: str) -> None:
        """Delete a user by ID"""
        User.delete_by_id(user_id)

    def authenticate(self, username_or_email: str, password: str) -> Dict[str, Any]:
        """Authenticate a user and return access token + profile."""
        user: Optional[User] = None
        # Find by username or email
        if "@" in username_or_email:
            user = User.query.filter_by(email=username_or_email).first()
        else:
            user = User.query.filter_by(username=username_or_email).first()
        if not user or not user.verify_password(password):
            logger.warning("Authentication failed for %s", username_or_email)
            raise ValueError("invalid_credentials")
        token = create_access_token(user.user_id)
        return {"access_token": token, "token_type": "bearer", "user": user.to_dict()}

    # Simple in-memory dict for password reset tokens; in production use DB/Redis
    _reset_tokens: Dict[str, str] = {}

    def start_password_reset(self, email: str) -> str:
        """Return a one-time reset token (UUID string)."""
        import uuid
        user = User.query.filter_by(email=email).first()
        if not user:
            raise ValueError("user_not_found")
        token = str(uuid.uuid4())
        self._reset_tokens[token] = user.user_id
        return token

    def confirm_password_reset(self, token: str, new_password: str):
        uid = self._reset_tokens.pop(token, None)
        if not uid:
            raise ValueError("invalid_or_expired_token")
        user = User.get_by_id(uid)
        user.set_password(new_password)
        db_session.commit()
        return user.to_dict()
