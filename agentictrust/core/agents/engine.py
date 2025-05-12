"""
Core agent management logic abstracted for reuse in routers and services
"""
from typing import List, Dict, Any, Optional
from agentictrust.db.models import Agent, Tool
from agentictrust.db.models.audit.agent_audit import AgentAuditLog

class AgentEngine:
    """Core engine for managing and enforcing agent lifecycle."""
    def __init__(self):
        # No internal state needed for now
        pass

    def register_agent(
        self,
        agent_name: str,
        description: Optional[str] = None,
        max_scope_level: str = 'restricted',
        tool_ids: List[str] = []
    ) -> Dict[str, Any]:
        """Create a new agent, associate tools, log audit, and return agent dict with credentials"""
        if not agent_name:
            raise ValueError("Missing agent_name")
        agent, client_secret = Agent.create(
            agent_name=agent_name,
            description=description,
            max_scope_level=max_scope_level
        )
        for tid in tool_ids or []:
            try:
                tool = Tool.get_by_id(tid)
                agent.add_tool(tool)
            except ValueError:
                # Skip invalid tool IDs
                continue
        AgentAuditLog.log(
            agent_id=agent.client_id,
            action="created",
            details={"agent_name": agent.agent_name}
        )
        return {
            "agent": agent.to_dict(),
            "credentials": {
                "client_id": agent.client_id,
                "client_secret": client_secret,
                "registration_token": agent.registration_token
            }
        }

    def activate_agent(self, registration_token: str) -> Dict[str, Any]:
        """Activate a registered agent by token, log audit, and return agent dict"""
        agent = Agent.find_by_registration_token(registration_token)
        agent.activate()
        AgentAuditLog.log(agent_id=agent.client_id, action="activated")
        return {"agent": agent.to_dict()}

    def get_agent(self, client_id: str) -> Dict[str, Any]:
        """Fetch agent by client_id and return dict"""
        agent = Agent.get_by_id(client_id)
        return agent.to_dict()

    def list_agents(self) -> List[Dict[str, Any]]:
        """List all agents as dicts"""
        return [agent.to_dict() for agent in Agent.list_all()]

    def delete_agent(self, client_id: str) -> None:
        """Delete an agent by client_id."""
        Agent.delete_by_id(client_id)
        AgentAuditLog.log(agent_id=client_id, action="deleted")

    def get_agent_tools(self, client_id: str) -> List[Dict[str, Any]]:
        """Get tools associated with an agent."""
        agent = Agent.get_by_id(client_id)
        return [tool.to_dict() for tool in agent.tools]

    def add_tool_to_agent(self, client_id: str, tool_id: str) -> Dict[str, Any]:
        """Add a tool to an agent."""
        agent = Agent.get_by_id(client_id)
        tool = Tool.get_by_id(tool_id)
        agent.add_tool(tool)
        AgentAuditLog.log(agent_id=client_id, action="add_tool", details={"tool_id": tool_id})
        return {"agent": agent.to_dict()}

    def remove_tool_from_agent(self, client_id: str, tool_id: str) -> Dict[str, Any]:
        """Remove a tool from an agent."""
        agent = Agent.get_by_id(client_id)
        tool = Tool.get_by_id(tool_id)
        agent.remove_tool(tool)
        AgentAuditLog.log(agent_id=client_id, action="remove_tool", details={"tool_id": tool_id})
        return {"agent": agent.to_dict()}

    def update_agent(self, client_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an agent's properties and tools."""
        agent = Agent.get_by_id(client_id)
        
        # Update basic properties using the agent's method
        properties_data = {k: v for k, v in data.items() if k in ['agent_name', 'description', 'max_scope_level']}
        if properties_data:
            agent.update_properties(properties_data)
            
        # Handle tool updates separately
        if 'tool_ids' in data:
            agent.tools = []
            for tid in data['tool_ids']:
                try:
                    tool = Tool.get_by_id(tid)
                    agent.add_tool(tool)
                except ValueError:
                    # Skip invalid tool IDs
                    pass
                    
        AgentAuditLog.log(agent_id=client_id, action="updated", details=data)
        return {"agent": agent.to_dict()}
