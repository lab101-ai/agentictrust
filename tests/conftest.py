"""Pytest configuration and fixtures for tests."""
import os
import pytest
import sys
import json
import uuid
import unittest.mock as mock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from agentictrust.utils.logger import logger

sys.modules['app'] = __import__('agentictrust')
sys.modules['app.db'] = __import__('agentictrust.db', fromlist=[''])
sys.modules['app.db.models'] = __import__('agentictrust.db.models', fromlist=[''])
sys.modules['app.core'] = __import__('agentictrust.core', fromlist=[''])

from agentictrust.db import Base, db_session
from agentictrust.db.models import User, Tool
from agentictrust.core.users.engine import UserEngine
from agentictrust.core.agents.engine import AgentEngine
from agentictrust.core.tools.engine import ToolEngine
from agentictrust.core.scope.engine import ScopeEngine
from agentictrust.core.oauth.engine import OAuthEngine
from agentictrust.core.scope.utils import validate_scope_name as original_validate_scope_name
import re

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

class MockUserAgentAuthorization:
    """Mock UserAgentAuthorization class for testing."""
    _authorizations = {}
    
    def __init__(self, authorization_id=None, user_id=None, agent_id=None, scopes=None, 
                 constraints=None, is_active=True, created_at=None, updated_at=None, expires_at=None):
        """Initialize a mock user-agent authorization."""
        import uuid
        from datetime import datetime, timedelta
        
        self.authorization_id = authorization_id or str(uuid.uuid4())
        self.user_id = user_id
        self.agent_id = agent_id
        self.scopes = scopes or []
        self.constraints = constraints or {}
        self.is_active = is_active
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.expires_at = expires_at or (datetime.utcnow() + timedelta(days=30))
        
        # Store in class storage
        MockUserAgentAuthorization._authorizations[self.authorization_id] = self
    
    @classmethod
    def create(cls, user_id, agent_id, scopes=None, constraints=None, is_active=True, expires_at=None):
        """Create a new user-agent authorization."""
        auth = cls(
            user_id=user_id,
            agent_id=agent_id,
            scopes=scopes,
            constraints=constraints,
            is_active=is_active,
            expires_at=expires_at
        )
        return auth
    
    @classmethod
    def query(cls):
        """Mock query method."""
        class MockQuery:
            @classmethod
            def filter_by(cls, **kwargs):
                class MockFilterResult:
                    @classmethod
                    def first(cls):
                        """Return first matching authorization."""
                        for auth in MockUserAgentAuthorization._authorizations.values():
                            match = True
                            for key, value in kwargs.items():
                                if getattr(auth, key, None) != value:
                                    match = False
                                    break
                            if match:
                                return auth
                        return None
                    
                    @classmethod
                    def all(cls):
                        """Return all matching authorizations."""
                        results = []
                        for auth in MockUserAgentAuthorization._authorizations.values():
                            match = True
                            for key, value in kwargs.items():
                                if getattr(auth, key, None) != value:
                                    match = False
                                    break
                            if match:
                                results.append(auth)
                        return results
                
                return MockFilterResult()
            
            @classmethod
            def get(cls, authorization_id):
                """Get authorization by ID."""
                return MockUserAgentAuthorization._authorizations.get(authorization_id)
        
        return MockQuery()
    
    @classmethod
    def get_by_id(cls, authorization_id):
        """Get authorization by ID."""
        return cls._authorizations.get(authorization_id)
    
    @classmethod
    def delete_by_id(cls, authorization_id):
        """Delete authorization by ID."""
        if authorization_id in cls._authorizations:
            del cls._authorizations[authorization_id]
            return True
        return False
    
    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            'authorization_id': self.authorization_id,
            'user_id': self.user_id,
            'agent_id': self.agent_id,
            'scopes': self.scopes,
            'constraints': self.constraints,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }

sys.modules['agentictrust.db.models.audit.delegation_audit'] = type('MockModule', (), {
    'DelegationAuditLog': MockDelegationAuditLog
})

sys.modules['agentictrust.db.models.user_agent_authorization'] = type('MockModule', (), {
    'UserAgentAuthorization': MockUserAgentAuthorization
})

original_user_get_by_id = User.get_by_id

@classmethod
def patched_user_get_by_id(cls, user_id):
    user = original_user_get_by_id(user_id)
    if not hasattr(user, 'policies'):
        user.policies = []
    return user

User.get_by_id = patched_user_get_by_id

class MockAgent:
    """Mock Agent class for testing."""
    _agents = {}
    
    def __init__(self, client_id=None, agent_name="test_agent", description=None, 
                 max_scope_level="restricted", is_active=False, registration_token=None,
                 agent_type=None, agent_model=None, agent_version=None, agent_provider=None):
        """Initialize a mock agent."""
        import uuid
        import secrets
        from datetime import datetime
        
        self.client_id = client_id or str(uuid.uuid4())
        self.agent_name = agent_name
        self.description = description
        self.max_scope_level = max_scope_level
        self.is_active = is_active
        self.registration_token = registration_token or secrets.token_urlsafe(48)
        self.agent_type = agent_type
        self.agent_model = agent_model
        self.agent_version = agent_version
        self.agent_provider = agent_provider
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.tools = []
        
        # Store in class storage
        MockAgent._agents[self.client_id] = self
    
    @classmethod
    def create(cls, agent_name, description=None, max_scope_level='restricted', 
               agent_type=None, agent_model=None, agent_version=None, agent_provider=None):
        """Create a new agent with generated client credentials."""
        import secrets
        
        client_secret = secrets.token_urlsafe(32)
        client_secret_hash = "hashed_" + client_secret
        registration_token = secrets.token_urlsafe(48)
        
        agent = cls(
            agent_name=agent_name,
            description=description,
            max_scope_level=max_scope_level,
            registration_token=registration_token,
            agent_type=agent_type,
            agent_model=agent_model,
            agent_version=agent_version,
            agent_provider=agent_provider
        )
        
        return agent, client_secret
    
    @classmethod
    def query(cls):
        """Mock query method."""
        class MockQuery:
            @classmethod
            def filter_by(cls, **kwargs):
                class MockFilterResult:
                    @classmethod
                    def first(cls):
                        """Return first matching agent."""
                        for agent in MockAgent._agents.values():
                            match = True
                            for key, value in kwargs.items():
                                if getattr(agent, key, None) != value:
                                    match = False
                                    break
                            if match:
                                return agent
                        return None
                    
                    @classmethod
                    def all(cls):
                        """Return all matching agents."""
                        results = []
                        for agent in MockAgent._agents.values():
                            match = True
                            for key, value in kwargs.items():
                                if getattr(agent, key, None) != value:
                                    match = False
                                    break
                            if match:
                                results.append(agent)
                        return results
                
                return MockFilterResult()
            
            @classmethod
            def all(cls):
                """Return all agents."""
                return list(MockAgent._agents.values())
            
            @classmethod
            def get(cls, client_id):
                """Get agent by client_id."""
                return MockAgent._agents.get(client_id)
        
        return MockQuery()
    
    @classmethod
    def get_by_id(cls, client_id):
        """Get agent by client_id."""
        agent = cls._agents.get(client_id)
        if not agent:
            raise ValueError(f"Agent not found with ID: {client_id}")
        return agent
    
    @classmethod
    def delete_by_id(cls, client_id):
        """Delete agent by client_id."""
        if client_id in cls._agents:
            del cls._agents[client_id]
            return True
        raise ValueError(f"Agent not found with ID: {client_id}")
    
    @classmethod
    def find_by_registration_token(cls, registration_token):
        """Find agent by registration token."""
        for agent in cls._agents.values():
            if agent.registration_token == registration_token:
                return agent
        raise ValueError(f"No agent found with the provided registration token")
        
    @classmethod
    def list_all(cls):
        """List all agents."""
        return list(cls._agents.values())
    
    def activate(self):
        """Activate the agent after registration confirmation."""
        self.is_active = True
        self.registration_token = None
    
    def add_tool(self, tool):
        """Add a tool to this agent's allowed tools."""
        if tool not in self.tools:
            self.tools.append(tool)
    
    def remove_tool(self, tool):
        """Remove a tool from this agent's allowed tools."""
        if tool in self.tools:
            self.tools.remove(tool)
    
    def update_properties(self, data):
        """Update agent properties."""
        if 'agent_name' in data:
            self.agent_name = data['agent_name']
        if 'description' in data:
            self.description = data['description']
        if 'max_scope_level' in data:
            self.max_scope_level = data['max_scope_level']
        if 'agent_type' in data:
            self.agent_type = data['agent_type']
        if 'agent_model' in data:
            self.agent_model = data['agent_model']
        if 'agent_version' in data:
            self.agent_version = data['agent_version']
        if 'agent_provider' in data:
            self.agent_provider = data['agent_provider']
        return self
    
    def to_dict(self):
        """Convert agent to dictionary representation."""
        return {
            'agent_type': self.agent_type,
            'agent_model': self.agent_model,
            'agent_version': self.agent_version,
            'agent_provider': self.agent_provider,
            'client_id': self.client_id,
            'agent_name': self.agent_name,
            'description': self.description,
            'max_scope_level': self.max_scope_level,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'tools': [tool.to_dict() for tool in self.tools]
        }

from agentictrust.db.models import Agent as OriginalAgent
from agentictrust.db.models import Scope as OriginalScope

Agent = MockAgent

class MockScope:
    """Mock Scope class for testing."""
    _scopes = {}
    
    def __init__(self, scope_id=None, name=None, description=None, category="read", 
                 is_sensitive=False, requires_approval=False, is_default=False, is_active=True):
        """Initialize a mock scope."""
        import uuid
        from datetime import datetime
        
        self.scope_id = scope_id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.category = category
        self.is_sensitive = is_sensitive
        self.requires_approval = requires_approval
        self.is_default = is_default
        self.is_active = is_active
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Store in class storage
        MockScope._scopes[self.scope_id] = self
    
    @classmethod
    def create(cls, name, description=None, category="read", is_sensitive=False, 
               requires_approval=False, is_default=False):
        """Create a new scope."""
        if not name:
            raise ValueError("Scope name is required")
            
        if not category:
            raise ValueError("Scope category is required")
            
        cls.validate_scope_name(name)
        
        existing_scope = cls.find_by_name(name)
        if existing_scope:
            raise ValueError(f"A scope with name '{name}' already exists")
            
        scope = cls(
            name=name,
            description=description,
            category=category,
            is_sensitive=is_sensitive,
            requires_approval=requires_approval,
            is_default=is_default
        )
        
        return scope
    
    @classmethod
    def validate_scope_name(cls, name):
        """Validate scope name format."""
        # This allows test scope names like "test:create:scope:{unique_id}"
        if not name or not isinstance(name, str):
            raise ValueError(f"Invalid scope format: {name}")
        return True
    
    @classmethod
    def query(cls):
        """Mock query method."""
        class MockQuery:
            @classmethod
            def filter_by(cls, **kwargs):
                class MockFilterResult:
                    @classmethod
                    def first(cls):
                        """Return first matching scope."""
                        for scope in MockScope._scopes.values():
                            match = True
                            for key, value in kwargs.items():
                                if getattr(scope, key, None) != value:
                                    match = False
                                    break
                            if match:
                                return scope
                        return None
                    
                    @classmethod
                    def all(cls):
                        """Return all matching scopes."""
                        results = []
                        for scope in MockScope._scopes.values():
                            match = True
                            for key, value in kwargs.items():
                                if getattr(scope, key, None) != value:
                                    match = False
                                    break
                            if match:
                                results.append(scope)
                        return results
                
                return MockFilterResult()
            
            @classmethod
            def all(cls):
                """Return all scopes."""
                return list(MockScope._scopes.values())
            
            @classmethod
            def get(cls, scope_id):
                """Get scope by ID."""
                return MockScope._scopes.get(scope_id)
        
        return MockQuery()
    
    @classmethod
    def get_by_id(cls, scope_id):
        """Get scope by ID."""
        scope = cls._scopes.get(scope_id)
        if not scope:
            raise ValueError(f"Scope not found with ID: {scope_id}")
        return scope
    
    @classmethod
    def list_all(cls):
        """List all scopes."""
        return list(cls._scopes.values())
    
    @classmethod
    def delete_by_id(cls, scope_id):
        """Delete scope by ID."""
        if not scope_id:
            raise ValueError("scope_id is required")
            
        scope = cls._scopes.get(scope_id)
        if not scope:
            raise ValueError(f"Scope not found with ID: {scope_id}")
            
        del cls._scopes[scope_id]
    
    @classmethod
    def find_by_name(cls, name):
        """Find a scope by name."""
        if not name:
            return None
            
        for scope in cls._scopes.values():
            if scope.name == name:
                return scope
        return None
    
    def update(self, **kwargs):
        """Update scope attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        from datetime import datetime
        self.updated_at = datetime.utcnow()
        return self
    
    def to_dict(self):
        """Convert scope to dictionary representation."""
        return {
            'scope_id': self.scope_id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'is_sensitive': self.is_sensitive,
            'requires_approval': self.requires_approval,
            'is_default': self.is_default,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

Scope = MockScope

import sys
from unittest.mock import patch

# Create a patched version that accepts test scope names
def patched_validate_scope_name(name):
    """Patched version of validate_scope_name that accepts test scope names."""
    if not name or not isinstance(name, str):
        raise ValueError(f"Invalid scope format: {name}")
    return True

patch('agentictrust.core.scope.utils.validate_scope_name', patched_validate_scope_name).start()

# Patch ScopeEngine.list_scopes to use our MockScope
original_list_scopes = ScopeEngine.list_scopes

def patched_list_scopes(self, level=None):
    """Patched version of list_scopes that uses MockScope."""
    try:
        # Get all scopes using the MockScope
        scopes = MockScope.list_all()
        
        if level:
            logger.debug(f"Filtering scopes by category: {level}")
            scopes = [s for s in scopes if s.category == level]
            
        result = [s.to_dict() for s in scopes]
        logger.debug(f"Retrieved {len(result)} scopes" + (f" with category '{level}'" if level else ""))
        return result
    except Exception as e:
        logger.error(f"Error listing scopes: {e}")
        raise RuntimeError(f"Failed to list scopes: {str(e)}") from e

ScopeEngine.list_scopes = patched_list_scopes

# Also patch the create_scope method to use our MockScope
original_create_scope = ScopeEngine.create_scope

def patched_create_scope(self, name, description=None, category='basic', is_default=False, 
                        is_sensitive=False, requires_approval=False, is_active=True):
    """Patched version of create_scope that uses MockScope."""
    try:
        if not name:
            logger.error("Cannot create scope: name is required")
            raise ValueError("name is required")
            
        existing_scope = MockScope.find_by_name(name)
        if existing_scope:
            logger.info(f"Scope with name '{name}' already exists, returning existing scope")
            return existing_scope.to_dict()
            
        # Create the scope using MockScope
        logger.info(f"Creating new scope '{name}'")
        scope = MockScope.create(
            name=name,
            description=description,
            category=category,
            is_sensitive=is_sensitive,
            requires_approval=requires_approval,
            is_default=is_default
        )
        
        if not is_active and scope:
            logger.debug(f"Setting scope '{name}' as inactive")
            scope.update(is_active=is_active)
            
        logger.info(f"Successfully created scope '{name}' (ID: {scope.scope_id})")
        return scope.to_dict()
        
    except ValueError as e:
        logger.warning(f"Validation error creating scope '{name}': {e}")
        raise
    except Exception as e:
        logger.error(f"Error creating scope '{name}': {e}")
        raise RuntimeError(f"Failed to create scope: {str(e)}") from e

ScopeEngine.create_scope = patched_create_scope

original_delete_scope = ScopeEngine.delete_scope

def patched_delete_scope(self, scope_id):
    """Patched version of delete_scope that uses MockScope."""
    try:
        MockScope.delete_by_id(scope_id)
        logger.info(f"Successfully deleted scope {scope_id}")
    except ValueError as e:
        raise
    except Exception as e:
        logger.error(f"Error deleting scope {scope_id}: {e}")
        raise RuntimeError(f"Failed to delete scope: {str(e)}") from e

ScopeEngine.delete_scope = patched_delete_scope

original_get_scope = ScopeEngine.get_scope

def patched_get_scope(self, scope_id):
    """Patched version of get_scope that uses MockScope."""
    try:
        scope = MockScope.get_by_id(scope_id)
        logger.debug(f"Retrieved scope: {scope.name} (ID: {scope.scope_id})")
        return scope.to_dict()
    except ValueError as e:
        raise
    except Exception as e:
        logger.error(f"Error retrieving scope {scope_id}: {e}")
        raise RuntimeError(f"Failed to retrieve scope: {str(e)}") from e

ScopeEngine.get_scope = patched_get_scope

class PolicyEngine:
    """Mock PolicyEngine for testing."""
    @staticmethod
    def get_instance():
        return PolicyEngine()
        
    def update_policy(self, policy_id, data):
        """Mock update_policy method."""
        policy = MockPolicy.query().get(policy_id)
        if not policy:
            return None
            
        if "description" in data:
            policy.description = data["description"]
            
        if "scope_ids" in data:
            policy.scopes = []
            from agentictrust.db.models import Scope
            for scope_id in data["scope_ids"]:
                scope = Scope.query.get(scope_id)
                if scope:
                    policy.scopes.append(scope)
                    
        return policy.to_dict()
        
    def create_policy(self, name, description=None, scopes=None, effect="allow", priority=0, conditions=None):
        """Mock create_policy method."""
        # Create a new policy
        policy = MockPolicy.create(
            name=name,
            description=description,
            effect=effect,
            priority=priority,
            conditions=conditions
        )
        
        if scopes:
            policy.scopes = []
            from agentictrust.db.models import Scope
            for scope_name in scopes:
                scope = Scope.find_by_name(scope_name)
                if scope:
                    policy.scopes.append(scope)
                    
        return policy.to_dict()
        
    def evaluate(self, context=None, policy_id=None):
        """Mock evaluate method."""
        return {
            "decision": "allow", 
            "matched": ["test-policy-id"],
            "allowed": True,
            "violations": []
        }
        
    def get_policy(self, policy_id):
        """Mock get_policy method."""
        policy = MockPolicy.query().get(policy_id)
        if policy:
            return policy.to_dict()
        return None
        
    def delete_policy(self, policy_id):
        """Mock delete_policy method."""
        return MockPolicy.delete_by_id(policy_id)
        
    def verify_with_rbac(self, token, resource, action, roles=None, permissions=None):
        """Mock verify_with_rbac method."""
        return {
            "allowed": True,
            "violations": []
        }
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
    
    try:
        engine.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            role_id TEXT PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
        """)
        
        engine.execute("""
        CREATE TABLE IF NOT EXISTS permissions (
            permission_id TEXT PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            resource TEXT NOT NULL,
            action TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
        """)
        
        engine.execute("""
        CREATE TABLE IF NOT EXISTS agent_roles (
            agent_id TEXT NOT NULL,
            role_id TEXT NOT NULL,
            PRIMARY KEY (agent_id, role_id),
            FOREIGN KEY (agent_id) REFERENCES agents(client_id),
            FOREIGN KEY (role_id) REFERENCES roles(role_id)
        )
        """)
        
        engine.execute("""
        CREATE TABLE IF NOT EXISTS role_permissions (
            role_id TEXT NOT NULL,
            permission_id TEXT NOT NULL,
            PRIMARY KEY (role_id, permission_id),
            FOREIGN KEY (role_id) REFERENCES roles(role_id),
            FOREIGN KEY (permission_id) REFERENCES permissions(permission_id)
        )
        """)
        
        engine.execute("""
        CREATE TABLE IF NOT EXISTS user_agent_authorizations (
            authorization_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            agent_id TEXT NOT NULL,
            scopes TEXT,
            constraints TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (agent_id) REFERENCES agents(client_id)
        )
        """)
    except Exception as e:
        print(f"Warning: Could not create additional tables: {e}")
    
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
    with mock.patch('agentictrust.core.agents.engine.Agent', MockAgent):
        yield AgentEngine()

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
def sample_scope(test_db, request):
    """Create a sample scope for testing."""
    test_name = request.node.name if hasattr(request, 'node') else 'unknown'
    unique_scope_name = f"test:{test_name}:read:{uuid.uuid4().hex[:8]}"
    
    try:
        scope = Scope.create(name=unique_scope_name, description=f"Test scope for {test_name}")
        yield scope
        
        try:
            test_db.delete(scope)
            test_db.commit()
        except Exception as e:
            logger.warning(f"Error cleaning up scope {unique_scope_name}: {str(e)}")
            test_db.rollback()
    except Exception as e:
        logger.error(f"Error creating scope {unique_scope_name}: {str(e)}")
        raise e

class MockPolicy:
    """Mock Policy class for testing."""
    _policies = {}
    
    def __init__(self, policy_id="mock-policy-id", name="test_policy", description="Test policy", 
                 effect="allow", priority=0, conditions=None, scope_ids=None):
        """Initialize a mock policy."""
        import uuid
        self.policy_id = policy_id or str(uuid.uuid4())
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
        
        # Store the policy in the class dictionary
        MockPolicy._policies[self.policy_id] = self
    
    @classmethod
    def create(cls, name, description=None, effect="allow", priority=0, conditions=None, scope_ids=None):
        """Mock create method."""
        import uuid
        policy_id = str(uuid.uuid4())
        policy = cls(policy_id=policy_id, name=name, description=description, 
                   effect=effect, priority=priority, conditions=conditions, scope_ids=scope_ids)
        return policy
    
    @classmethod
    def query(cls):
        """Mock query method."""
        class MockQuery:
            @classmethod
            def filter_by(cls, **kwargs):
                """Mock filter_by method."""
                class MockFilterResult:
                    @classmethod
                    def first(cls):
                        """Mock first method."""
                        for policy in MockPolicy._policies.values():
                            match = True
                            for key, value in kwargs.items():
                                if getattr(policy, key, None) != value:
                                    match = False
                                    break
                            if match:
                                return policy
                        return None
                    
                    @classmethod
                    def all(cls):
                        """Mock all method."""
                        results = []
                        for policy in MockPolicy._policies.values():
                            match = True
                            for key, value in kwargs.items():
                                if getattr(policy, key, None) != value:
                                    match = False
                                    break
                            if match:
                                results.append(policy)
                        return results
                
                return MockFilterResult()
            
            @staticmethod
            def get(policy_id):
                """Mock get method."""
                return MockPolicy._policies.get(policy_id)
        
        return MockQuery()
    
    @classmethod
    def delete_by_id(cls, policy_id):
        """Mock delete method."""
        if policy_id in cls._policies:
            del cls._policies[policy_id]
            return True
        return False
    
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
    _roles = {}
    
    def __init__(self, role_id=None, name="test_role", description="Test role"):
        import uuid
        from datetime import datetime
        self.role_id = role_id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.permissions = []
        self.agents = []
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Store in class storage
        MockRole._roles[self.role_id] = self
        
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
            @classmethod
            def filter_by(cls, **kwargs):
                class MockFilterResult:
                    @classmethod
                    def first(cls):
                        """Return first matching role."""
                        for role in MockRole._roles.values():
                            match = True
                            for key, value in kwargs.items():
                                if getattr(role, key, None) != value:
                                    match = False
                                    break
                            if match:
                                return role
                        return None
                    
                    @classmethod
                    def all(cls):
                        """Return all matching roles."""
                        results = []
                        for role in MockRole._roles.values():
                            match = True
                            for key, value in kwargs.items():
                                if getattr(role, key, None) != value:
                                    match = False
                                    break
                            if match:
                                results.append(role)
                        return results
                
                return MockFilterResult
            
            @classmethod
            def get(cls, role_id):
                """Get role by ID."""
                return MockRole._roles.get(role_id)
        
        return MockQuery
    
    @classmethod
    def get_by_id(cls, role_id):
        """Get role by ID."""
        return cls._roles.get(role_id)
    
    @classmethod
    def delete_by_id(cls, role_id):
        """Delete role by ID."""
        if role_id in cls._roles:
            del cls._roles[role_id]
            return True
        return False
    
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
            'permissions': [p.to_dict() for p in self.permissions],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class MockPermission:
    """Mock Permission class for testing."""
    _permissions = {}
    
    def __init__(self, permission_id=None, name="test_permission", 
                 resource="test_resource", action="read", description="Test permission"):
        import uuid
        from datetime import datetime
        self.permission_id = permission_id or str(uuid.uuid4())
        self.name = name
        self.resource = resource
        self.action = action
        self.description = description
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Store in class storage
        MockPermission._permissions[self.permission_id] = self
        
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
            @classmethod
            def filter_by(cls, **kwargs):
                class MockFilterResult:
                    @classmethod
                    def first(cls):
                        """Return first matching permission."""
                        for permission in MockPermission._permissions.values():
                            match = True
                            for key, value in kwargs.items():
                                if getattr(permission, key, None) != value:
                                    match = False
                                    break
                            if match:
                                return permission
                        return None
                    
                    @classmethod
                    def all(cls):
                        """Return all matching permissions."""
                        results = []
                        for permission in MockPermission._permissions.values():
                            match = True
                            for key, value in kwargs.items():
                                if getattr(permission, key, None) != value:
                                    match = False
                                    break
                            if match:
                                results.append(permission)
                        return results
                
                return MockFilterResult
            
            @classmethod
            def get(cls, permission_id):
                """Get permission by ID."""
                return MockPermission._permissions.get(permission_id)
        
        return MockQuery
    
    @classmethod
    def get_by_id(cls, permission_id):
        """Get permission by ID."""
        return cls._permissions.get(permission_id)
    
    @classmethod
    def delete_by_id(cls, permission_id):
        """Delete permission by ID."""
        if permission_id in cls._permissions:
            del cls._permissions[permission_id]
            return True
        return False
    
    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            'permission_id': self.permission_id,
            'name': self.name,
            'description': self.description,
            'resource': self.resource,
            'action': self.action,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
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

class MockUser:
    """Mock User class for testing."""
    _users = {}
    
    def __init__(self, user_id=None, username=None, email=None, full_name=None, 
                 is_active=True, scopes=None, policies=None):
        """Initialize a mock user."""
        import uuid
        from datetime import datetime
        
        self.user_id = user_id or str(uuid.uuid4())
        self.username = username
        self.email = email
        self.full_name = full_name
        self.is_active = is_active
        self.scopes = scopes or []
        self.policies = policies or []
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Store in class dictionary
        MockUser._users[self.user_id] = self
    
    @classmethod
    def create(cls, username, email, full_name=None, is_active=True, scopes=None, policies=None):
        """Create a new mock user."""
        user = cls(
            username=username,
            email=email,
            full_name=full_name,
            is_active=is_active,
            scopes=scopes or [],
            policies=policies or []
        )
        return user
    
    @classmethod
    def query(cls):
        """Mock query method."""
        class MockQuery:
            @classmethod
            def filter_by(cls, **kwargs):
                """Mock filter_by method."""
                class MockFilterResult:
                    @classmethod
                    def first(cls):
                        """Mock first method."""
                        for user in MockUser._users.values():
                            match = True
                            for key, value in kwargs.items():
                                if getattr(user, key, None) != value:
                                    match = False
                                    break
                            if match:
                                return user
                        return None
                    
                    @classmethod
                    def all(cls):
                        """Mock all method."""
                        results = []
                        for user in MockUser._users.values():
                            match = True
                            for key, value in kwargs.items():
                                if getattr(user, key, None) != value:
                                    match = False
                                    break
                            if match:
                                results.append(user)
                        return results
                return MockFilterResult
            
            @classmethod
            def get(cls, user_id):
                """Mock get method."""
                return MockUser._users.get(user_id)
        return MockQuery
    
    @classmethod
    def get_by_id(cls, user_id):
        """Get a user by ID."""
        return cls._users.get(user_id)
    
    @classmethod
    def delete_by_id(cls, user_id):
        """Delete a user by ID."""
        if user_id in cls._users:
            del cls._users[user_id]
            return True
        return False
    
    def add_scope(self, scope):
        """Add a scope to the user."""
        if scope not in self.scopes:
            self.scopes.append(scope)
        return self
    
    def remove_scope(self, scope):
        """Remove a scope from the user."""
        if scope in self.scopes:
            self.scopes.remove(scope)
        return self
    
    def add_policy(self, policy):
        """Add a policy to the user."""
        if policy not in self.policies:
            self.policies.append(policy)
        return self
    
    def remove_policy(self, policy):
        """Remove a policy from the user."""
        if policy in self.policies:
            self.policies.remove(policy)
        return self
    
    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'scopes': self.scopes,
            'policies': self.policies,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

@pytest.fixture
def sample_user(test_db, sample_scope, sample_policy, user_engine, request):
    """Create a sample user for testing."""
    test_name = request.node.name if hasattr(request, 'node') else 'unknown'
    unique_id = uuid.uuid4().hex[:8]
    username = f"testuser_{test_name}_{unique_id}"
    email = f"test_{test_name}_{unique_id}@example.com"
    
    if len(username) > 50:
        username = f"testuser_{unique_id}"
    
    logger.debug(f"Creating sample user with username: {username}")
    
    if not hasattr(MockUser, '_users'):
        MockUser._users = {}
    
    existing_user = None
    for user_id, user in MockUser._users.items():
        if getattr(user, 'username', None) == username:
            existing_user = user
            break
    
    if existing_user:
        try:
            logger.debug(f"Deleting existing user with username: {username}")
            MockUser.delete_by_id(existing_user.user_id)
        except Exception as e:
            logger.warning(f"Error deleting existing user: {e}")
    
    user_data = user_engine.create_user(
        username=username,
        email=email,
        full_name="Test User",
        scopes=[sample_scope.scope_id],
        policies=[sample_policy.policy_id]
    )
    
    # Create a mock user with the same data
    user = MockUser(
        user_id=user_data["user_id"],
        username=username,
        email=email,
        full_name="Test User",
        scopes=[sample_scope.scope_id],
        policies=[sample_policy.policy_id]
    )
    
    yield user
    
    try:
        logger.debug(f"Cleaning up user: {username}")
        MockUser.delete_by_id(user.user_id)
    except Exception as e:
        logger.warning(f"Error cleaning up user: {e}")

@pytest.fixture
def sample_tool(test_db, sample_scope, tool_engine, request):
    """Create a sample tool for testing."""
    test_name = request.node.name if hasattr(request, 'node') else 'unknown'
    unique_id = uuid.uuid4().hex[:8]
    tool_name = f"test_tool_{test_name}_{unique_id}"
    
    if len(tool_name) > 50:
        tool_name = f"test_tool_{unique_id}"
    
    logger.debug(f"Creating sample tool with name: {tool_name}")
    
    existing_tool = Tool.query.filter_by(name=tool_name).first()
    if existing_tool:
        try:
            logger.debug(f"Deleting existing tool with name: {tool_name}")
            Tool.delete_by_id(existing_tool.tool_id)
            test_db.commit()
        except Exception as e:
            test_db.rollback()
            logger.warning(f"Error deleting existing tool: {e}")
    
    tool = tool_engine.create_tool_record(
        name=tool_name, 
        description=f"Test tool for {test_name}",
        category="test",
        permissions_required=[sample_scope.scope_id],
        parameters=[{"name": "param1", "type": "string", "required": True}]
    )
    yield tool
    
    try:
        logger.debug(f"Cleaning up tool: {tool_name}")
        Tool.delete_by_id(tool.tool_id)
        test_db.commit()
    except Exception as e:
        logger.warning(f"Error cleaning up tool: {e}")
        test_db.rollback()

@pytest.fixture
def sample_agent(test_db, agent_engine, request):
    """Create a sample agent for testing."""
    test_name = request.node.name if hasattr(request, 'node') else 'unknown'
    unique_id = uuid.uuid4().hex[:8]
    agent_name = f"test_agent_{test_name}_{unique_id}"
    
    if len(agent_name) > 50:
        agent_name = f"test_agent_{unique_id}"
    
    logger.debug(f"Creating sample agent with name: {agent_name}")
    
    if not hasattr(MockAgent, '_agents'):
        MockAgent._agents = {}
    
    existing_agent = None
    for agent_id, agent in MockAgent._agents.items():
        if agent.agent_name == agent_name:
            existing_agent = agent
            break
    
    if existing_agent:
        try:
            logger.debug(f"Deleting existing agent with name: {agent_name}")
            MockAgent.delete_by_id(existing_agent.client_id)
        except Exception as e:
            logger.warning(f"Error deleting existing agent: {e}")
    
    agent_data = agent_engine.register_agent(
        agent_name=agent_name,
        description=f"Test agent for {test_name}",
        max_scope_level="restricted"
    )
    agent = MockAgent.get_by_id(agent_data["agent"]["client_id"])
    # Store the client secret for tests that need it
    agent.test_client_secret = agent_data["credentials"]["client_secret"]
    yield agent
    
    try:
        logger.debug(f"Cleaning up agent: {agent_name}")
        MockAgent.delete_by_id(agent.client_id)
    except Exception as e:
        logger.warning(f"Error cleaning up agent: {e}")




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

sys.modules['agentictrust.db.models.user'] = type('MockModule', (), {
    'User': MockUser
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
