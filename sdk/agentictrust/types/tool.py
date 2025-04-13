"""
Type definitions for tool-related objects.
"""
from typing import Dict, List, Optional, Any, TypedDict, Union


class ParameterDict(TypedDict, total=False):
    """Type definition for a tool parameter."""
    name: str
    type: str
    description: Optional[str]
    required: bool
    default: Any


class ToolDict(TypedDict, total=False):
    """Type definition for a tool object."""
    tool_id: str
    name: str
    description: Optional[str]
    category: Optional[str]
    permissions_required: List[str]
    parameters: List[ParameterDict]
    inputSchema: Dict[str, Any]
    is_active: bool
    created_at: str
    updated_at: str


class ToolListResponse(TypedDict):
    """Type definition for the response from listing tools."""
    tools: List[ToolDict]
    total: int
    page: int
    per_page: int


class ToolAccessResponseDict(TypedDict, total=False):
    """Type definition for the tool access verification response."""
    access_allowed: bool
    tool_name: str
    token_id: str
    task_id: str
    reason: Optional[str]
    scopes_required: Optional[List[str]]
    available_scopes: Optional[List[str]]
