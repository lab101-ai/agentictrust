from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class Auth0UserRequest(BaseModel):
    auth0_id: str
    email: str
    full_name: Optional[str] = None
    auth0_metadata: Optional[Dict[str, Any]] = None
    social_provider: Optional[str] = None
    social_provider_id: Optional[str] = None

class CreateUserRequest(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    hashed_password: Optional[str] = None  # Optional for Auth0 users
    is_external: Optional[bool] = False
    department: Optional[str] = None
    job_title: Optional[str] = None
    level: Optional[str] = None
    scopes: Optional[List[str]] = []
    auth0_id: Optional[str] = None
    auth0_metadata: Optional[Dict[str, Any]] = None
    social_provider: Optional[str] = None
    social_provider_id: Optional[str] = None

class UpdateUserRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    hashed_password: Optional[str] = None
    is_external: Optional[bool] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    level: Optional[str] = None
    scopes: Optional[List[str]] = None
    auth0_id: Optional[str] = None
    auth0_metadata: Optional[Dict[str, Any]] = None
    social_provider: Optional[str] = None
    social_provider_id: Optional[str] = None
    last_login: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None

class UserProfile(BaseModel):
    user_id: str
    username: str
    email: str
    full_name: Optional[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    is_external: bool
    scopes: List[str]
    auth0_metadata: Optional[Dict[str, Any]] = None
    picture: Optional[str] = None
