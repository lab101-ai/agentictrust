"""Pytest configuration and fixtures for tests."""
import os
import pytest
import sys
import json
import unittest.mock as mock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

class MockDelegationAuditLog:
    """Mock DelegationAuditLog class for testing."""
    _audit_logs = {}
    
    def __init__(self, log_id=None, principal_id=None, principal_type=None, delegate_id=None, 
                 delegate_type=None, token_id=None, operation=None, status=None, scopes=None, 
                 purpose=None, context=None, parent_token_id=None):
        import uuid
        
        self.log_id = log_id or str(uuid.uuid4())
        self.principal_id = principal_id
        self.principal_type = principal_type
        self.delegate_id = delegate_id
        self.delegate_type = delegate_type
        self.token_id = token_id
        self.operation = operation
        self.status = status
        self.scopes = scopes or []
        self.purpose = purpose
        self.context = context or {}
        self.parent_token_id = parent_token_id
        self.timestamp = datetime.utcnow()
        
        # Store this instance in the class storage
        MockDelegationAuditLog._audit_logs[self.log_id] = self
    
    @classmethod
    def create(cls, principal_id, principal_type, delegate_id, delegate_type, token_id, 
               operation, status, scopes=None, purpose=None, context=None, parent_token_id=None):
        """Create a new delegation audit log."""
        log = cls(
            principal_id=principal_id,
            principal_type=principal_type,
            delegate_id=delegate_id,
            delegate_type=delegate_type,
            token_id=token_id,
            operation=operation,
            status=status,
            scopes=scopes,
            purpose=purpose,
            context=context,
            parent_token_id=parent_token_id
        )
        return log
    
    @classmethod
    def log_event(cls, grant_id=None, action=None, principal_id=None, delegate_id=None, 
                  token_id=None, scope=None, context=None, status="success"):
        """Log a delegation event."""
        return cls.create(
            principal_id=principal_id,
            principal_type="user",
            delegate_id=delegate_id,
            delegate_type="agent",
            token_id=token_id,
            operation=action,
            status=status,
            scopes=scope,
            context=context or {}
        )
    
    @classmethod
    def get_delegation_chain(cls, token_id):
        """Get the delegation chain for a token."""
        chain = []
        for log in cls._audit_logs.values():
            if log.token_id == token_id or (log.parent_token_id and log.parent_token_id == token_id):
                chain.append(log)
                
        chain.sort(key=lambda x: x.timestamp)
        
        for log in chain:
            if log.parent_token_id:
                for parent_log in cls._audit_logs.values():
                    if parent_log.token_id == log.parent_token_id and parent_log not in chain:
                        chain.insert(0, parent_log)
                        
        return chain
    
    @classmethod
    def get_user_delegation_activity(cls, user_id):
        """Get delegation activity for a user."""
        delegations_as_principal = []
        delegations_as_delegate = []
        
        for log in cls._audit_logs.values():
            if log.principal_id == user_id:
                delegations_as_principal.append(log)
            if log.delegate_id == user_id:
                delegations_as_delegate.append(log)
                
        return {
            "user_id": user_id,
            "delegations_as_principal": delegations_as_principal,
            "delegations_as_delegate": delegations_as_delegate,
            "delegated_tokens": []  # Mock empty list for tokens
        }
        
    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            'log_id': self.log_id,
            'principal_id': self.principal_id,
            'principal_type': self.principal_type,
            'delegate_id': self.delegate_id,
            'delegate_type': self.delegate_type,
            'token_id': self.token_id,
            'operation': self.operation,
            'status': self.status,
            'scopes': self.scopes,
            'purpose': self.purpose,
            'context': self.context,
            'parent_token_id': self.parent_token_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
        
    @classmethod
    def delete(cls, instance):
        """Delete an audit log from the storage."""
        if instance.log_id in cls._audit_logs:
            del cls._audit_logs[instance.log_id]
            return True
        return False

sys.modules['agentictrust.db.models.audit.delegation_audit'] = type('MockModule', (), {
    'DelegationAuditLog': MockDelegationAuditLog
})

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
        
    def update_policy(self, policy_id, data):
        """Mock update_policy method."""
        policy = MockPolicy.query.get(policy_id)
        if not policy:
            return None
        return policy
        
    def evaluate(self, policy_id=None, context=None):
        """Mock evaluate method."""
        return {"allow": True}
        
    def get_policy(self, policy_id):
        """Mock get_policy method."""
        return MockPolicy.query.get(policy_id)
        
    def delete_policy(self, policy_id):
        """Mock delete_policy method."""
        return MockPolicy.delete_by_id(policy_id)
from agentictrust.core.oauth.engine import OAuthEngine

@pytest.fixture(scope="session")
def test_db():
    """Create a test database in memory."""
    # Use SQLite in-memory for tests
    engine = create_engine("sqlite:///:memory:")
    
    from agentictrust.db.models import (
        Agent, AuthorizationCode, Tool, TaskAuditLog,
        Scope, User, ScopeAuditLog, TokenAuditLog, AgentAuditLog,
        DelegationGrant, DelegationAuditLog
    )
    from agentictrust.db.models import IssuedToken
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create a new session factory
    Session = sessionmaker(bind=engine)
    
    # Replace the db_session with our test session
    original_session = db_session.registry()
    db_session.configure(bind=engine)
    
    # DelegationAuditLog is already mocked at the module level
    
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
    existing_scope = Scope.query.filter_by(name="test:read").first()
    if existing_scope:
        yield existing_scope
        return
        
    try:
        scope = Scope.create(name="test:read", description="Test read scope")
        yield scope
        test_db.delete(scope)
        test_db.commit()
    except Exception as e:
        existing_scope = Scope.query.filter_by(name="test:read").first()
        if existing_scope:
            yield existing_scope
        else:
            raise e

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

class MockRole:
    """Mock Role class for testing."""
    
    def __init__(self, role_id="mock-role-id", name="test_role", description="Test role"):
        self.role_id = role_id
        self.name = name
        self.description = description
        self.permissions = []
        self.agents = []
        
    @classmethod
    def create(cls, name, description=None):
        """Mock create method."""
        import uuid
        role_id = str(uuid.uuid4())
        return cls(role_id=role_id, name=name, description=description)
    
    @classmethod
    def query(cls):
        """Mock query method."""
        class MockQuery:
            @staticmethod
            def filter_by(name=None):
                class MockFilterResult:
                    @staticmethod
                    def first():
                        return MockRole(name=name)
                return MockFilterResult()
                
            @staticmethod
            def get(role_id):
                return MockRole(role_id=role_id)
        
        return MockQuery()
    
    def add_permission(self, permission):
        """Add a permission to this role."""
        if permission not in self.permissions:
            self.permissions.append(permission)
    
    def remove_permission(self, permission):
        """Remove a permission from this role."""
        if permission in self.permissions:
            self.permissions.remove(permission)
    
    def get_permissions(self):
        """Get permissions for this role."""
        return self.permissions
        
    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            'role_id': self.role_id,
            'name': self.name,
            'description': self.description,
            'permissions': [p.to_dict() for p in self.permissions]
        }

class MockPermission:
    """Mock Permission class for testing."""
    
    def __init__(self, permission_id="mock-permission-id", name="test_permission", 
                 resource="test_resource", action="read", description="Test permission"):
        self.permission_id = permission_id
        self.name = name
        self.resource = resource
        self.action = action
        self.description = description
        
    @classmethod
    def create(cls, name, resource, action, description=None):
        """Mock create method."""
        import uuid
        permission_id = str(uuid.uuid4())
        return cls(permission_id=permission_id, name=name, resource=resource, 
                   action=action, description=description)
    
    @classmethod
    def query(cls):
        """Mock query method."""
        class MockQuery:
            @staticmethod
            def filter_by(name=None):
                class MockFilterResult:
                    @staticmethod
                    def first():
                        return MockPermission(name=name)
                return MockFilterResult()
                
            @staticmethod
            def get(permission_id):
                return MockPermission(permission_id=permission_id)
        
        return MockQuery()
    
    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            'permission_id': self.permission_id,
            'name': self.name,
            'description': self.description,
            'resource': self.resource,
            'action': self.action
        }

class MockUserAgentAuthorization:
    """Mock UserAgentAuthorization class for testing."""
    _authorizations = {}
    
    @classmethod
    def delete(cls, instance):
        """Delete an authorization from the storage."""
        if instance.authorization_id in cls._authorizations:
            del cls._authorizations[instance.authorization_id]
            return True
        return False
    
    def __init__(self, authorization_id="mock-auth-id", user_id=None, agent_id=None, 
                 scopes=None, constraints=None, is_active=True):
        import uuid
        from datetime import datetime
        self.authorization_id = authorization_id
        self.user_id = user_id
        self.agent_id = agent_id
        self.scopes = scopes or "read:data write:data"
        self.constraints = constraints or {}
        self.is_active = is_active
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.expires_at = None
        self.user = None
        self.agent = None
        
        # Store this instance in the class storage
        MockUserAgentAuthorization._authorizations[self.authorization_id] = self
        
    @classmethod
    def check_authorization(cls, user_id, agent_id, requested_scopes=None):
        """Check if a user has authorized an agent with the requested scopes."""
        auth = cls.get_by_user_and_agent(user_id, agent_id)
        if not auth or not auth.is_active:
            return False
            
        if requested_scopes:
            auth_scopes = auth.scopes
            if isinstance(auth_scopes, str):
                auth_scopes = auth_scopes.split()
                
            for scope in requested_scopes:
                if scope not in auth_scopes:
                    return False
                    
        return True
        
    @classmethod
    def create(cls, user_id, agent_id, scopes, constraints=None, ttl_days=None):
        """Mock create method."""
        import uuid
        authorization_id = str(uuid.uuid4())
        if isinstance(scopes, list):
            scopes = ' '.join(scopes)
        auth = cls(authorization_id=authorization_id, user_id=user_id, agent_id=agent_id, 
                   scopes=scopes, constraints=constraints)
        return auth
    
    @classmethod
    def query(cls):
        """Mock query method."""
        class MockQuery:
            @staticmethod
            def filter_by(user_id=None, agent_id=None, is_active=None):
                class MockFilterResult:
                    @staticmethod
                    def first():
                        # Return the first matching authorization
                        for auth in MockUserAgentAuthorization._authorizations.values():
                            if ((user_id is None or auth.user_id == user_id) and
                                (agent_id is None or auth.agent_id == agent_id) and
                                (is_active is None or auth.is_active == is_active)):
                                return auth
                        return None
                    
                    @staticmethod
                    def all():
                        result = []
                        for auth in MockUserAgentAuthorization._authorizations.values():
                            if ((user_id is None or auth.user_id == user_id) and
                                (agent_id is None or auth.agent_id == agent_id) and
                                (is_active is None or auth.is_active == is_active)):
                                result.append(auth)
                        return result
                return MockFilterResult()
                
            @staticmethod
            def get(authorization_id):
                return MockUserAgentAuthorization._authorizations.get(authorization_id)
        
        return MockQuery()
    
    @classmethod
    def get_by_id(cls, authorization_id):
        """Get authorization by ID."""
        return MockUserAgentAuthorization._authorizations.get(authorization_id)
    
    @classmethod
    def get_by_user_and_agent(cls, user_id, agent_id, active_only=True):
        """Get authorization by user and agent IDs."""
        for auth in cls._authorizations.values():
            if (auth.user_id == user_id and 
                auth.agent_id == agent_id and 
                (not active_only or auth.is_active)):
                return auth
        return None
    
    @classmethod
    def list_by_user(cls, user_id, active_only=False):
        """List all authorizations for a user."""
        result = []
        for auth in cls._authorizations.values():
            if auth.user_id == user_id and (not active_only or auth.is_active):
                result.append(auth)
        return result
    
    @classmethod
    def list_by_agent(cls, agent_id, active_only=False):
        """List all authorizations for an agent."""
        result = []
        for auth in cls._authorizations.values():
            if auth.agent_id == agent_id and (not active_only or auth.is_active):
                result.append(auth)
        return result
    
    @classmethod
    def delete_by_id(cls, authorization_id):
        """Mock delete method."""
        if authorization_id in cls._authorizations:
            del cls._authorizations[authorization_id]
            return True
        return False
    
    def revoke(self):
        """Revoke this authorization."""
        self.is_active = False
        # Update the stored authorization
        MockUserAgentAuthorization._authorizations[self.authorization_id] = self
        return self
    
    def update(self, scopes=None, constraints=None, is_active=None, ttl_days=None):
        """Update authorization properties."""
        if scopes is not None:
            if isinstance(scopes, list):
                scopes = ' '.join(scopes)
            self.scopes = scopes
            
        if constraints is not None:
            self.constraints = constraints
            
        if is_active is not None:
            self.is_active = is_active
        
        # Update the stored authorization
        MockUserAgentAuthorization._authorizations[self.authorization_id] = self
        return self
    
    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            'authorization_id': self.authorization_id,
            'user_id': self.user_id,
            'agent_id': self.agent_id,
            'scopes': self.scopes.split(' ') if isinstance(self.scopes, str) else self.scopes,
            'constraints': self.constraints,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'agent': self.agent.to_dict() if self.agent else None,
        }

@pytest.fixture
def sample_policy(test_db):
    """Create a mock policy for testing."""
    policy = MockPolicy()
    yield policy

@pytest.fixture
def sample_user(test_db, sample_scope, sample_policy, user_engine):
    """Create a sample user for testing."""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    username = f"testuser_{unique_id}"
    email = f"test_{unique_id}@example.com"
    
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        try:
            User.delete_by_id(existing_user.user_id)
            test_db.commit()
        except Exception as e:
            test_db.rollback()
            print(f"Error deleting existing user: {e}")
    
    user_data = user_engine.create_user(
        username=username,
        email=email,
        full_name="Test User",
        scopes=[sample_scope.scope_id],
        policies=[sample_policy.policy_id]
    )
    user = User.get_by_id(user_data["user_id"])
    yield user
    try:
        User.delete_by_id(user.user_id)
    except Exception as e:
        print(f"Error cleaning up user: {e}")
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




sys.modules['agentictrust.db.models.user_agent_authorization'] = type('MockModule', (), {
    'UserAgentAuthorization': MockUserAgentAuthorization
})

sys.modules['agentictrust.db.models.role'] = type('MockModule', (), {
    'Role': MockRole
})

sys.modules['agentictrust.db.models.permission'] = type('MockModule', (), {
    'Permission': MockPermission
})

from tests.mock_issued_token import MockIssuedToken

sys.modules['agentictrust.db.models.token'] = type('MockModule', (), {
    'IssuedToken': MockIssuedToken
})

@pytest.fixture
def sample_user_agent_authorization(test_db, sample_user, sample_agent):
    """Create a sample user-agent authorization for testing."""
    auth = MockUserAgentAuthorization.create(
        user_id=sample_user.user_id,
        agent_id=sample_agent.client_id,
        scopes=["read:data", "write:data"],
        constraints={"time_restrictions": {"start_hour": 9, "end_hour": 17}}
    )
    auth.user = sample_user
    auth.agent = sample_agent
    yield auth
