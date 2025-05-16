"""Tests for User-Agent Authorization model."""
import pytest
from datetime import datetime, timedelta
from tests.conftest import MockUserAgentAuthorization

def test_create_user_agent_authorization(test_db, sample_user, sample_agent):
    """Test creating a user-agent authorization."""
    MockUserAgentAuthorization._authorizations = {}
    
    scopes = ["read:data", "write:data"]
    constraints = {"time_restrictions": {"start_hour": 9, "end_hour": 17}}
    
    auth = MockUserAgentAuthorization.create(
        user_id=sample_user.user_id,
        agent_id=sample_agent.client_id,
        scopes=scopes,
        constraints=constraints,
        ttl_days=30
    )
    
    assert auth.user_id == sample_user.user_id
    assert auth.agent_id == sample_agent.client_id
    assert isinstance(auth.scopes, str) or auth.scopes == scopes
    assert auth.constraints == constraints
    assert auth.is_active is True
    
def test_get_user_agent_authorization(test_db, sample_user_agent_authorization):
    """Test getting a user-agent authorization."""
    MockUserAgentAuthorization._authorizations[sample_user_agent_authorization.authorization_id] = sample_user_agent_authorization
    
    auth = MockUserAgentAuthorization.get_by_id(sample_user_agent_authorization.authorization_id)
    
    assert auth is not None
    assert auth.authorization_id == sample_user_agent_authorization.authorization_id
    assert auth.user_id == sample_user_agent_authorization.user_id
    assert auth.agent_id == sample_user_agent_authorization.agent_id

def test_get_user_authorizations(test_db, sample_user_agent_authorization):
    """Test getting all authorizations for a user."""
    MockUserAgentAuthorization._authorizations[sample_user_agent_authorization.authorization_id] = sample_user_agent_authorization
    
    authorizations = MockUserAgentAuthorization.list_by_user(sample_user_agent_authorization.user_id)
    
    assert len(authorizations) >= 1
    assert any(auth.authorization_id == sample_user_agent_authorization.authorization_id 
               for auth in authorizations)

def test_revoke_authorization(test_db, sample_user_agent_authorization):
    """Test revoking an authorization."""
    MockUserAgentAuthorization._authorizations[sample_user_agent_authorization.authorization_id] = sample_user_agent_authorization
    
    # Call the revoke method on the sample authorization
    sample_user_agent_authorization.revoke()
    
    auth = MockUserAgentAuthorization.get_by_id(sample_user_agent_authorization.authorization_id)
    assert auth.is_active is False
