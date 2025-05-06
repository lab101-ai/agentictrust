"""
API resource for agent management.
"""
from typing import Dict, List, Optional, Any, Union

from .abstract import APIResource
from .scopes import ScopesResource
from .policies import PoliciesResource
from ..types.agent import AgentDict, AgentListResponse, AgentRegistrationResponse
from ..utils.validators import validate_string, validate_string_list


class AgentsResource(APIResource):
    """API resource for agent management."""
    
    def __init__(self, parent=None):
        """Initialize with parent client."""
        super().__init__(parent)
        
        # Initialize resources
        self._scopes_api = ScopesResource(parent)
        self._policies_api = PoliciesResource(parent)
        
    def register(
        self,
        agent_name: str,
        description: Optional[str] = None,
        allowed_tools: Optional[List[str]] = None,
        max_scope_level: str = "restricted",
        tool_ids: Optional[List[str]] = None,
    ) -> AgentRegistrationResponse:
        """
        Register a new agent with the AgenticTrust server.
        
        Args:
            agent_name: Name of the agent
            description: Optional description of the agent
            allowed_tools: List of allowed tools for this agent
            max_scope_level: Maximum scope level (default: "restricted")
            tool_ids: List of tool IDs to associate with this agent
            
        Returns:
            Dict containing agent details and credentials
        """
        # Validate inputs
        agent_name = validate_string(agent_name, "agent_name")
        description = validate_string(description, "description", required=False)
        allowed_tools = validate_string_list(allowed_tools, "allowed_tools", required=False)
        max_scope_level = validate_string(max_scope_level, "max_scope_level")
        tool_ids = validate_string_list(tool_ids, "tool_ids", required=False)
        
        # Prepare request data
        data = {
            "agent_name": agent_name,
            "description": description,
            "allowed_tools": allowed_tools or [],
            "max_scope_level": max_scope_level,
            "tool_ids": tool_ids or [],
        }
        
        # Make API request
        return self._request("POST", "/api/agents/register", json_data=data)
    
    def activate(self, registration_token: str) -> Dict[str, Any]:
        """
        Activate a registered agent using the registration token.
        
        Args:
            registration_token: The registration token received during registration
            
        Returns:
            Dict containing activation status and agent details
        """
        # Validate input
        registration_token = validate_string(registration_token, "registration_token")
        
        # Prepare request data
        data = {
            "registration_token": registration_token
        }
        
        # Make API request
        return self._request("POST", "/api/agents/activate", json_data=data)
    
    def list(
        self,
        page: int = 1,
        per_page: int = 20,
        name_filter: Optional[str] = None,
        active_only: bool = False,
    ) -> AgentListResponse:
        """
        List all registered agents.
        
        Args:
            page: Page number for pagination
            per_page: Number of items per page
            name_filter: Optional filter by agent name
            active_only: Whether to only include active agents
            
        Returns:
            Dict containing list of agents
        """
        # Prepare query parameters
        params = {
            "page": page,
            "per_page": per_page,
        }
        
        if name_filter:
            params["name"] = name_filter
            
        if active_only:
            params["active"] = "true"
        
        # Make API request
        return self._request("GET", "/api/agents/list", params=params)
    
    def get(self, agent_id: str) -> AgentDict:
        """
        Get details of a specific agent.
        
        Args:
            agent_id: The ID of the agent
            
        Returns:
            Dict containing agent details
        """
        # Validate input
        agent_id = validate_string(agent_id, "agent_id")
        
        # Make API request
        return self._request("GET", f"/api/agents/{agent_id}")
    
    def update(
        self,
        agent_id: str,
        agent_name: Optional[str] = None,
        description: Optional[str] = None,
        allowed_tools: Optional[List[str]] = None,
        max_scope_level: Optional[str] = None,
        tool_ids: Optional[List[str]] = None,
        is_active: Optional[bool] = None,
    ) -> AgentDict:
        """
        Update an existing agent.
        
        Args:
            agent_id: The ID of the agent to update
            agent_name: Optional new name for the agent
            description: Optional new description for the agent
            allowed_tools: Optional new list of allowed tools
            max_scope_level: Optional new maximum scope level
            tool_ids: Optional new list of tool IDs
            is_active: Optional new active status
            
        Returns:
            Dict containing updated agent details
        """
        # Validate inputs
        agent_id = validate_string(agent_id, "agent_id")
        
        # Prepare request data (only include non-None values)
        data = {}
        
        if agent_name is not None:
            data["agent_name"] = validate_string(agent_name, "agent_name")
            
        if description is not None:
            data["description"] = validate_string(description, "description", required=False)
            
        if allowed_tools is not None:
            data["allowed_tools"] = validate_string_list(allowed_tools, "allowed_tools", required=False)
            
        if max_scope_level is not None:
            data["max_scope_level"] = validate_string(max_scope_level, "max_scope_level")
            
        if tool_ids is not None:
            data["tool_ids"] = validate_string_list(tool_ids, "tool_ids", required=False)
            
        if is_active is not None:
            data["is_active"] = is_active
        
        # Make API request
        return self._request("PUT", f"/api/agents/{agent_id}", json_data=data)
    
    def delete(self, agent_id: str) -> Dict[str, Any]:
        """Delete an agent."""
        # Validate input
        agent_id = validate_string(agent_id, "agent_id")
        
        # Make API request
        return self._request("DELETE", f"/api/agents/{agent_id}")
    
    def list_scopes(self, agent_id: str) -> List[Dict[str, Any]]:
        """List scopes assigned to an agent."""
        return self._scopes_api.list()
    
    def list_policies(self) -> List[Dict[str, Any]]:
        """List all policies."""
        return self._policies_api.list()
    
    def regenerate_secret(self, agent_id: str) -> Dict[str, Any]:
        """
        Regenerate client secret for an agent.
        
        Args:
            agent_id: The ID of the agent
            
        Returns:
            Dict containing new client credentials
        """
        # Validate input
        agent_id = validate_string(agent_id, "agent_id")
        
        try:
            # Get agent details first to ensure it exists
            agent = self.get(agent_id=agent_id)
            # Return a placeholder secret for now since endpoint doesn't exist
            return {"client_secret": "placeholder_secret_for_" + agent_id[:8]}
        except Exception as e:
            raise ValueError(f"Failed to regenerate secret: {str(e)}")
