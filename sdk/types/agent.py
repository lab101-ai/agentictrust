"""
Type definitions for agent-related objects.
"""
from typing import Dict, List, Optional, Any, TypedDict


class AgentDict(TypedDict, total=False):
    """Type definition for an agent object."""
    agent_id: str
    agent_name: str
    description: Optional[str]
    allowed_tools: List[str]
    max_scope_level: str
    client_id: str
    client_secret: str
    registration_token: str
    is_active: bool
    created_at: str
    updated_at: str
    tool_ids: List[str]


class AgentListResponse(TypedDict):
    """Type definition for the response from listing agents."""
    agents: List[AgentDict]
    total: int
    page: int
    per_page: int


class AgentRegistrationResponse(TypedDict, total=False):
    """Type definition for the response from registering an agent."""
    agent_id: str
    agent_name: str
    client_id: str
    client_secret: str
    registration_token: str
    status: str
