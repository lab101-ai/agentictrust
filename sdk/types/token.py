"""
Type definitions for token-related objects.
"""
from typing import Dict, List, Optional, Any, TypedDict, Union


class ParentTokenDict(TypedDict, total=False):
    """Type definition for a parent token reference."""
    token: str
    task_id: str


class TokenRequestDict(TypedDict, total=False):
    """Type definition for a token request."""
    client_id: str
    client_secret: str
    scope: Union[List[str], str]
    task_id: Optional[str]
    task_description: Optional[str]
    required_tools: Optional[List[str]]
    parent_task_id: Optional[str]
    parent_token: Optional[str]
    scope_inheritance_type: str
    code_challenge: Optional[str]
    code_challenge_method: str
    parent_tokens: Optional[List[ParentTokenDict]]


class TokenResponseDict(TypedDict, total=False):
    """Type definition for a token response."""
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str]
    scope: str
    task_id: str
    agent_id: str
    client_id: str
    issued_at: int
    parent_task_id: Optional[str]


class TokenIntrospectionDict(TypedDict, total=False):
    """Type definition for token introspection results."""
    active: bool
    scope: str
    client_id: str
    agent_id: str
    agent_name: str
    exp: int
    iat: int
    token_id: str
    task_id: str
    task_description: Optional[str]
    parent_task_id: Optional[str]
    required_tools: List[str]
    scope_inheritance_type: str
    children: Optional[List['TokenIntrospectionDict']]
    task_history: Optional[List[Dict[str, Any]]]
