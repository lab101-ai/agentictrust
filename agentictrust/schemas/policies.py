from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class CreatePolicyRequest(BaseModel):
    name: str
    description: Optional[str] = None
    scopes: Optional[List[str]] = []
    effect: Optional[str] = 'allow'
    priority: Optional[int] = 10
    conditions: Optional[Dict[str, Any]] = {}

class UpdatePolicyRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    scopes: Optional[List[str]] = None
    effect: Optional[str] = None
    priority: Optional[int] = None
    conditions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

# Response schemas for policies
class PolicyResponse(BaseModel):
    policy_id: str
    name: str
    description: Optional[str]
    scopes: List[str]
    effect: str
    priority: int
    conditions: Dict[str, Any]
    is_active: bool
    created_at: Optional[str]
    updated_at: Optional[str]

class CreatePolicyResponse(BaseModel):
    message: str
    policy: PolicyResponse

class ListPoliciesResponse(BaseModel):
    policies: List[PolicyResponse]

class BasicResponse(BaseModel):
    message: str

# Policy check schemas
class AuthorizationData(BaseModel):
    """Authorization data includes user details and token information."""
    user_id: str
    username: str
    department: str
    partner: str
    scopes: List[str]
    token_id: Optional[str] = None
    parent_token_id: Optional[str] = None

class RequestData(BaseModel):
    """Data about the request being authorized."""
    action: str
    resource: Dict[str, Any]

class PolicyCheckRequest(BaseModel):
    """Request to check if an action is authorized."""
    auth: AuthorizationData
    request: RequestData

class PolicyCheckResponse(BaseModel):
    """Response from a policy check."""
    allowed: bool
    message: str
    decision_id: str
