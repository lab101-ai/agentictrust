"""Integration tests between users, agents, and tools."""
import pytest
from app.db.models import User, Agent, Tool, Scope, Policy
from app.core.users.engine import UserEngine
from app.core.agents.engine import AgentEngine
from app.core.tools.engine import ToolEngine

def test_end_to_end_workflow(test_db, user_engine, agent_engine, tool_engine):
    """Test the full workflow of creating users, agents, and tools and their interactions."""
    # Step 1: Create a scope for permissions
    scope = Scope.create(name="integration:data:read", description="Permission to read data")
    
    # Step 2: Create a policy
    policy = Policy.create(
        name="basic_access", 
        description="Basic access policy",
        conditions={"user": {"department": "QA"}}
    )
    
    # Step 3: Create a user with the scope and policy
    user_data = user_engine.create_user(
        username="integration_user",
        email="integration@example.com",
        full_name="Integration Test User",
        department="QA",
        scopes=[scope.scope_id],
        policies=[policy.policy_id]
    )
    user_id = user_data["user_id"]
    
    # Step 4: Create a tool requiring the scope
    tool = tool_engine.create_tool_record(
        name="data_retrieval_tool",
        description="Tool for retrieving data",
        category="data",
        permissions_required=[scope.scope_id],
        parameters=[
            {"name": "query", "type": "string", "required": True},
            {"name": "limit", "type": "integer", "required": False}
        ]
    )
    
    # Step 5: Register an agent
    agent_data = agent_engine.register_agent(
        agent_name="data_assistant",
        description="Agent for data retrieval",
        max_scope_level="standard"
    )
    agent_id = agent_data["agent"]["client_id"]
    
    # Step 6: Associate the tool with the agent
    agent_engine.add_tool_to_agent(agent_id, tool.tool_id)
    
    # Step 7: Activate the agent
    registration_token = agent_data["credentials"]["registration_token"]
    agent_engine.activate_agent(registration_token)
    
    # Verify the association between all components
    
    # Check if agent has access to the tool
    agent_tools = agent_engine.get_agent_tools(agent_id)
    assert len(agent_tools) == 1
    assert agent_tools[0]["name"] == "data_retrieval_tool"
    
    # Check if the tool requires the scope that the user has
    tool_data = tool_engine.get_tool(tool.tool_id)
    assert scope.scope_id in tool_data["permissions_required"]
    
    # Get user to verify their scopes
    user = User.get_by_id(user_id)
    user_scopes = [s.scope_id for s in user.scopes]
    assert scope.scope_id in user_scopes
    
    # Clean up
    Agent.delete_by_id(agent_id)
    Tool.delete_by_id(tool.tool_id)
    User.delete_by_id(user_id)
    test_db.delete(policy)
    test_db.delete(scope)
    test_db.commit()

def test_agent_with_multiple_tools(test_db, agent_engine, tool_engine, sample_scope):
    """Test an agent with multiple tools."""
    # Create tools
    tool1 = tool_engine.create_tool_record(
        name="multi_tool_1",
        description="First multi-tool test",
        category="test",
        permissions_required=[sample_scope.scope_id],
        parameters=[]
    )
    
    tool2 = tool_engine.create_tool_record(
        name="multi_tool_2",
        description="Second multi-tool test",
        category="test",
        permissions_required=[sample_scope.scope_id],
        parameters=[]
    )
    
    # Create agent with both tools
    agent_data = agent_engine.register_agent(
        agent_name="multi_tool_agent",
        description="Agent with multiple tools",
        tool_ids=[tool1.tool_id, tool2.tool_id]
    )
    
    agent_id = agent_data["agent"]["client_id"]
    
    # Verify agent has both tools
    agent_tools = agent_engine.get_agent_tools(agent_id)
    assert len(agent_tools) == 2
    tool_names = {tool["name"] for tool in agent_tools}
    assert "multi_tool_1" in tool_names
    assert "multi_tool_2" in tool_names
    
    # Update agent to remove one tool
    agent_engine.update_agent(
        agent_id,
        {"tool_ids": [tool1.tool_id]}  # Only keep the first tool
    )
    
    # Verify agent now has only one tool
    agent_tools = agent_engine.get_agent_tools(agent_id)
    assert len(agent_tools) == 1
    assert agent_tools[0]["name"] == "multi_tool_1"
    
    # Clean up
    Agent.delete_by_id(agent_id)
    Tool.delete_by_id(tool1.tool_id)
    Tool.delete_by_id(tool2.tool_id)

def test_user_with_multiple_agents(test_db, user_engine, agent_engine):
    """Test scenario with a user having multiple agents."""
    # Create user
    user_data = user_engine.create_user(
        username="multi_agent_user",
        email="multiagent@example.com"
    )
    user_id = user_data["user_id"]
    
    # Create agents (in a real scenario, agents might be created by the user)
    agent1_data = agent_engine.register_agent(agent_name="user_agent_1")
    agent2_data = agent_engine.register_agent(agent_name="user_agent_2")
    
    # In a real application, there might be a user-agent association table
    # Here we're simulating that relationship by updating user attributes
    user_engine.update_user(
        user_id,
        {"attributes": {"agent_ids": [
            agent1_data["agent"]["client_id"], 
            agent2_data["agent"]["client_id"]
        ]}}
    )
    
    # Verify user has the agent IDs in attributes
    updated_user = User.get_by_id(user_id)
    assert "agent_ids" in updated_user.attributes
    assert len(updated_user.attributes["agent_ids"]) == 2
    
    # Clean up
    User.delete_by_id(user_id)
    Agent.delete_by_id(agent1_data["agent"]["client_id"])
    Agent.delete_by_id(agent2_data["agent"]["client_id"])
