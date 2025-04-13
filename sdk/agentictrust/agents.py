"""
Client for agent registration and management.
"""
from typing import Dict, List, Optional, Any, Union

from .api_resources.agents import AgentsResource
from .types.agent import AgentDict, AgentListResponse, AgentRegistrationResponse
from .utils.validators import validate_string, validate_string_list


class AgentClient:
    """
    Client for agent registration and management.
    """
    
    def __init__(self, parent=None):
        """
        Initialize with parent client.
        
        Args:
            parent: Parent AgenticTrustClient instance
        """
        self.parent = parent
        self._api = AgentsResource(parent)
    
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
        return self._api.register(
            agent_name=agent_name,
            description=description,
            allowed_tools=allowed_tools,
            max_scope_level=max_scope_level,
            tool_ids=tool_ids,
        )
    
    def activate(self, registration_token: str) -> Dict[str, Any]:
        """
        Activate a registered agent using the registration token.
        
        Args:
            registration_token: The registration token received during registration
            
        Returns:
            Dict containing activation status and agent details
        """
        return self._api.activate(registration_token=registration_token)
    
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
        return self._api.list(
            page=page,
            per_page=per_page,
            name_filter=name_filter,
            active_only=active_only,
        )
    
    def get(self, agent_id: str) -> AgentDict:
        """
        Get details of a specific agent.
        
        Args:
            agent_id: The ID of the agent
            
        Returns:
            Dict containing agent details
        """
        return self._api.get(agent_id=agent_id)
    
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
        return self._api.update(
            agent_id=agent_id,
            agent_name=agent_name,
            description=description,
            allowed_tools=allowed_tools,
            max_scope_level=max_scope_level,
            tool_ids=tool_ids,
            is_active=is_active,
        )
    
    def delete(self, agent_id: str) -> Dict[str, Any]:
        """
        Delete an agent.
        
        Args:
            agent_id: The ID of the agent to delete
            
        Returns:
            Dict containing deletion status
        """
        return self._api.delete(agent_id=agent_id)
    
    def regenerate_secret(self, agent_id: str) -> Dict[str, Any]:
        """
        Regenerate client secret for an agent.
        
        Args:
            agent_id: The ID of the agent
            
        Returns:
            Dict containing new client credentials
        """
        return self._api.regenerate_secret(agent_id=agent_id)
