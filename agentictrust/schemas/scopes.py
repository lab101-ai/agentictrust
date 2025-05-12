from pydantic import BaseModel
from typing import Optional, List

class CreateScopeRequest(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = 'basic'
    is_default: Optional[bool] = False
    is_sensitive: Optional[bool] = False
    requires_approval: Optional[bool] = False
    is_active: Optional[bool] = True

class UpdateScopeRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_default: Optional[bool] = None
    is_sensitive: Optional[bool] = None
    requires_approval: Optional[bool] = None
    is_active: Optional[bool] = None

class ExpandRequest(BaseModel):
    scopes: List[str]

class ExpandResponse(BaseModel):
    expanded: List[str]

class ScopeRegistryItem(BaseModel):
    name: str
    resource: str
    action: str
    qualifiers: List[str]
    description: Optional[str]

class ScopeRegistryResponse(BaseModel):
    registry: List[ScopeRegistryItem]

class ScopeResponse(BaseModel):
    scope_id: str
    name: str
    description: Optional[str]
    category: str
    is_sensitive: bool
    requires_approval: bool
    is_default: bool
    is_active: bool
    created_at: Optional[str]
    updated_at: Optional[str]

class CreateScopeResponse(BaseModel):
    message: str
    scope: ScopeResponse

class ListScopesResponse(BaseModel):
    scopes: List[ScopeResponse]

class BasicResponse(BaseModel):
    message: str
