from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class CreateUserAgentAuthorizationRequest(BaseModel):
    """Request model for creating a user-agent authorization."""
    user_id: str = Field(..., description="ID of the user granting authorization")
    agent_id: str = Field(..., description="ID of the agent being authorized")
    scopes: List[str] = Field(..., description="List of scopes to grant to the agent")
    constraints: Optional[Dict[str, Any]] = Field(None, description="Optional constraints on the authorization")
    ttl_days: Optional[int] = Field(None, description="Time-to-live in days for this authorization")

class UpdateUserAgentAuthorizationRequest(BaseModel):
    """Request model for updating a user-agent authorization."""
    scopes: Optional[List[str]] = Field(None, description="Updated list of scopes")
    constraints: Optional[Dict[str, Any]] = Field(None, description="Updated constraints")
    is_active: Optional[bool] = Field(None, description="Whether the authorization is active")
    ttl_days: Optional[int] = Field(None, description="Updated time-to-live in days")

class UserAgentAuthorizationResponse(BaseModel):
    """Response model for user-agent authorization."""
    authorization_id: str
    user_id: str
    agent_id: str
    scopes: List[str]
    constraints: Dict[str, Any]
    is_active: bool
    created_at: str
    updated_at: str
    expires_at: Optional[str] = None
    agent: Optional[Dict[str, Any]] = None
