"""Pytest configuration and fixtures for tests."""
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db import Base, db_session
from app.db.models import User, Agent, Tool, Scope, Policy
from app.core.users.engine import UserEngine
from app.core.agents.engine import AgentEngine
from app.core.tools.engine import ToolEngine

@pytest.fixture(scope="session")
def test_db():
    """Create a test database in memory."""
    # Use SQLite in-memory for tests
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    # Create a new session factory
    Session = sessionmaker(bind=engine)
    
    # Replace the db_session with our test session
    original_session = db_session.registry()
    db_session.configure(bind=engine)
    
    # Setup done, yield control to the tests
    yield db_session
    
    # Teardown: restore original session
    db_session.configure(bind=original_session.bind)

@pytest.fixture
def user_engine():
    """Provide a UserEngine instance."""
    return UserEngine()

@pytest.fixture
def agent_engine():
    """Provide an AgentEngine instance."""
    return AgentEngine()

@pytest.fixture
def tool_engine():
    """Provide a ToolEngine instance."""
    return ToolEngine()

@pytest.fixture
def sample_scope(test_db):
    """Create a sample scope for testing."""
    scope = Scope.create(name="test:read", description="Test read scope")
    yield scope
    test_db.delete(scope)
    test_db.commit()

@pytest.fixture
def sample_policy(test_db):
    """Create a sample policy for testing."""
    policy = Policy.create(
        name="test_policy", 
        description="Test policy",
        conditions={"environment": {"type": "test"}}
    )
    yield policy
    test_db.delete(policy)
    test_db.commit()

@pytest.fixture
def sample_user(test_db, sample_scope, sample_policy, user_engine):
    """Create a sample user for testing."""
    user_data = user_engine.create_user(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        scopes=[sample_scope.scope_id],
        policies=[sample_policy.policy_id]
    )
    user = User.get_by_id(user_data["user_id"])
    yield user
    try:
        User.delete_by_id(user.user_id)
    except:
        pass

@pytest.fixture
def sample_tool(test_db, sample_scope, tool_engine):
    """Create a sample tool for testing."""
    tool = tool_engine.create_tool_record(
        name="test_tool", 
        description="Test tool for testing",
        category="test",
        permissions_required=[sample_scope.scope_id],
        parameters=[{"name": "param1", "type": "string", "required": True}]
    )
    yield tool
    try:
        Tool.delete_by_id(tool.tool_id)
    except:
        pass

@pytest.fixture
def sample_agent(test_db, agent_engine):
    """Create a sample agent for testing."""
    agent_data = agent_engine.register_agent(
        agent_name="test_agent",
        description="Test agent for testing",
        max_scope_level="restricted"
    )
    agent = Agent.get_by_id(agent_data["agent"]["client_id"])
    # Store the client secret for tests that need it
    agent.test_client_secret = agent_data["credentials"]["client_secret"]
    yield agent
    try:
        Agent.delete_by_id(agent.client_id)
    except:
        pass
