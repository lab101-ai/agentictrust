"""Pydantic schemas for UserAgentAuthorization endpoints."""
from typing import List, Optional
from pydantic import BaseModel, Field


class AuthorizationCreateRequest(BaseModel):
    user_id: str = Field(..., description="ID of the human user")
    agent_id: str = Field(..., description="client_id of the agent")
    scopes: List[str] = Field(..., description="List of scope IDs being granted")


class AuthorizationOut(BaseModel):
    authorization_id: str
    user_id: str
    agent_id: str
    scopes: List[str]
    created_at: str
    revoked_at: Optional[str] = None
    is_active: bool
