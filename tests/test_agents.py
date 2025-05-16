"""End-to-end tests for agent management."""
import pytest
from tests.conftest import MockAgent as Agent

def test_register_agent(test_db, agent_engine):
    """Test registering a new agent."""
    # Register a new agent
    agent_data = agent_engine.register_agent(
        agent_name="test_register_agent",
        description="Agent created in test",
        max_scope_level="restricted"
    )
    
    # Verify agent data
    assert "agent" in agent_data
    assert "credentials" in agent_data
    assert agent_data["agent"]["agent_name"] == "test_register_agent"
    assert agent_data["agent"]["description"] == "Agent created in test"
    assert agent_data["agent"]["max_scope_level"] == "restricted"
    assert agent_data["agent"]["is_active"] is False
    
    # Verify credentials
    assert "client_id" in agent_data["credentials"]
    assert "client_secret" in agent_data["credentials"]
    assert "registration_token" in agent_data["credentials"]
    
    # Verify agent exists in database
    agent = Agent.get_by_id(agent_data["agent"]["client_id"])
    assert agent is not None
    assert agent.agent_name == "test_register_agent"
    
    # Clean up
    Agent.delete_by_id(agent_data["agent"]["client_id"])

def test_activate_agent(test_db, agent_engine):
    """Test activating an agent with a registration token."""
    # Register a new agent
    agent_data = agent_engine.register_agent(
        agent_name="activation_test_agent"
    )
    registration_token = agent_data["credentials"]["registration_token"]
    
    # Verify agent is not active
    agent = Agent.get_by_id(agent_data["agent"]["client_id"])
    assert agent.is_active is False
    assert agent.registration_token is not None
    
    # Activate the agent
    activation_data = agent_engine.activate_agent(registration_token)
    
    # Verify activation
    assert "agent" in activation_data
    assert activation_data["agent"]["is_active"] is True
    
    # Verify database was updated
    agent = Agent.get_by_id(agent_data["agent"]["client_id"])
    assert agent.is_active is True
    assert agent.registration_token is None
    
    # Clean up
    Agent.delete_by_id(agent_data["agent"]["client_id"])

def test_get_agent(test_db, sample_agent, agent_engine):
    """Test getting an agent by client_id."""
    # Get the agent
    agent_data = agent_engine.get_agent(sample_agent.client_id)
    
    # Verify agent data
    assert agent_data["client_id"] == sample_agent.client_id
    assert agent_data["agent_name"] == sample_agent.agent_name

def test_list_agents(test_db, sample_agent, agent_engine):
    """Test listing all agents."""
    # Get all agents
    agents = agent_engine.list_agents()
    
    # Verify sample agent is in the list
    client_ids = [agent["client_id"] for agent in agents]
    assert sample_agent.client_id in client_ids

def test_update_agent(test_db, sample_agent, agent_engine):
    """Test updating an agent."""
    # Update the agent
    update_data = {
        "agent_name": "Updated Agent",
        "description": "Updated description",
        "max_scope_level": "extended"
    }
    result = agent_engine.update_agent(
        sample_agent.client_id, 
        update_data
    )
    
    # Verify update was successful
    updated_agent = result["agent"]
    assert updated_agent["agent_name"] == "Updated Agent"
    assert updated_agent["description"] == "Updated description"
    assert updated_agent["max_scope_level"] == "extended"
    
    # Verify database was updated
    agent = Agent.get_by_id(sample_agent.client_id)
    assert agent.agent_name == "Updated Agent"
    assert agent.description == "Updated description"
    assert agent.max_scope_level == "extended"

def test_delete_agent(test_db, agent_engine):
    """Test deleting an agent."""
    # Create an agent to delete
    agent_data = agent_engine.register_agent(
        agent_name="agent_to_delete"
    )
    client_id = agent_data["agent"]["client_id"]
    
    # Verify agent exists
    agent = Agent.get_by_id(client_id)
    assert agent is not None
    
    # Delete the agent
    agent_engine.delete_agent(client_id)
    
    # Verify agent no longer exists
    with pytest.raises(ValueError, match="Agent not found"):
        Agent.get_by_id(client_id)

def test_agent_tool_association(test_db, sample_agent, sample_tool, agent_engine):
    """Test adding and removing tools from an agent."""
    # Add tool to agent
    result = agent_engine.add_tool_to_agent(
        sample_agent.client_id,
        sample_tool.tool_id
    )
    
    # Verify tool was added
    agent = Agent.get_by_id(sample_agent.client_id)
    assert len(agent.tools) == 1
    assert agent.tools[0].tool_id == sample_tool.tool_id
    
    # Get tools associated with agent
    tools = agent_engine.get_agent_tools(sample_agent.client_id)
    assert len(tools) == 1
    assert tools[0]["tool_id"] == sample_tool.tool_id
    
    # Remove tool from agent
    result = agent_engine.remove_tool_from_agent(
        sample_agent.client_id,
        sample_tool.tool_id
    )
    
    # Verify tool was removed
    agent = Agent.get_by_id(sample_agent.client_id)
    assert len(agent.tools) == 0
