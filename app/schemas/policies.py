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
