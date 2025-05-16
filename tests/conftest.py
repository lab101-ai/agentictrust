"""Pytest configuration and fixtures for tests."""
import os
import pytest
import sys
import json
import unittest.mock as mock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.modules['app'] = __import__('agentictrust')
sys.modules['app.db'] = __import__('agentictrust.db', fromlist=[''])
sys.modules['app.db.models'] = __import__('agentictrust.db.models', fromlist=[''])
sys.modules['app.core'] = __import__('agentictrust.core', fromlist=[''])

from agentictrust.db import Base, db_session
from agentictrust.db.models import User, Agent, Tool, Scope
from agentictrust.core.users.engine import UserEngine
from agentictrust.core.agents.engine import AgentEngine
from agentictrust.core.tools.engine import ToolEngine
from agentictrust.core.scope.engine import ScopeEngine
class PolicyEngine:
    """Mock PolicyEngine for testing."""
    @staticmethod
    def get_instance():
        return PolicyEngine()
from agentictrust.core.oauth.engine import OAuthEngine

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
def scope_engine():
    """Provide a ScopeEngine instance."""
    return ScopeEngine()

@pytest.fixture
def policy_engine():
    """Provide a PolicyEngine instance."""
    return PolicyEngine()

@pytest.fixture
def oauth_engine():
    """Provide a OAuthEngine instance."""
    return OAuthEngine()

@pytest.fixture
def sample_scope(test_db):
    """Create a sample scope for testing."""
    scope = Scope.create(name="test:read", description="Test read scope")
    yield scope
    test_db.delete(scope)
    test_db.commit()

class MockPolicy:
    """Mock Policy class for testing."""
    
    def __init__(self, policy_id="mock-policy-id", name="test_policy", description="Test policy", 
                 effect="allow", priority=0, conditions=None, scope_ids=None):
        self.policy_id = policy_id
        self.name = name
        self.description = description
        self.effect = effect
        self.priority = priority
        self.conditions = conditions or {"environment": {"type": "test"}}
        self.scopes = []
        
        if scope_ids:
            from agentictrust.db.models import Scope
            for scope_id in scope_ids:
                scope = Scope.query.get(scope_id)
                if scope:
                    self.scopes.append(scope)
    
    @classmethod
    def create(cls, name, description=None, effect="allow", priority=0, conditions=None, scope_ids=None):
        """Mock create method."""
        import uuid
        policy_id = str(uuid.uuid4())
        return cls(policy_id=policy_id, name=name, description=description, 
                   effect=effect, priority=priority, conditions=conditions, scope_ids=scope_ids)
    
    @classmethod
    def query(cls):
        """Mock query method."""
        class MockQuery:
            @staticmethod
            def filter_by(name=None):
                class MockFilterResult:
                    @staticmethod
                    def first():
                        return MockPolicy(name=name)
                return MockFilterResult()
                
            @staticmethod
            def get(policy_id):
                return MockPolicy(policy_id=policy_id)
        
        return MockQuery()
    
    @classmethod
    def delete_by_id(cls, policy_id):
        """Mock delete method."""
        return True
    
    def to_dict(self):
        """Convert policy to dictionary."""
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "description": self.description,
            "effect": self.effect,
            "priority": self.priority,
            "conditions": self.conditions,
            "scopes": [scope.name for scope in self.scopes]
        }

@pytest.fixture
def sample_policy(test_db):
    """Create a mock policy for testing."""
    policy = MockPolicy()
    yield policy

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



@pytest.fixture
def sample_user_agent_authorization(test_db, sample_user, sample_agent):
    """Create a sample user-agent authorization for testing."""
    from agentictrust.db.models.user_agent_authorization import UserAgentAuthorization
    auth = UserAgentAuthorization.create(
        user_id=sample_user.user_id,
        agent_id=sample_agent.client_id,
        scopes=["read:data", "write:data"],
        constraints={"time_restrictions": {"start_hour": 9, "end_hour": 17}}
    )
    yield auth
    try:
        UserAgentAuthorization.delete_by_id(auth.authorization_id)
    except:
        pass
