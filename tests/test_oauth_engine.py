"""Tests for the refactored OAuthEngine."""
import pytest
import secrets
from datetime import datetime, timedelta
from app.db.models import Agent, IssuedToken
from app.db.models.authorization_code import AuthorizationCode
from app.core.oauth.utils import pkce_verify

def test_create_authorization_code(test_db, oauth_engine):
    """Test creating an authorization code using the refactored OAuth engine."""
    client_id = "test-client"
    redirect_uri = "https://example.com/callback"
    code_challenge = "test_challenge"
    state = "test_state"
    
    # Create authorization code via engine
    code, returned_state = oauth_engine.create_authorization_code(
        client_id=client_id,
        redirect_uri=redirect_uri,
        code_challenge=code_challenge,
        state=state,
        scope="test:scope"  # Adding the required scope parameter
    )
    
    # Verify code was created and state returned
    assert code is not None
    assert len(code) > 20  # Should be a long random string
    assert returned_state == state
    
    # Verify code exists in database
    auth_code = AuthorizationCode.query.filter_by(client_id=client_id).first()
    assert auth_code is not None
    assert auth_code.redirect_uri == redirect_uri
    assert auth_code.code_challenge == code_challenge
    
    # Clean up
    db_codes = AuthorizationCode.query.filter_by(client_id=client_id).all()
    for code in db_codes:
        AuthorizationCode.query.filter_by(code_id=code.code_id).delete()
    test_db.commit()

def test_revoke_token(test_db, oauth_engine):
    """Test revoking a token using the refactored OAuth engine."""
    # Create an agent
    agent_name = "test_revoke_agent"
    agent, _ = Agent.create(agent_name=agent_name)
    
    # Create a token to revoke
    token_obj, _, _ = IssuedToken.create(
        client_id=agent.client_id,
        scope=["test:scope"],
        granted_tools=[],
        task_id="test-task",
        agent_instance_id=agent.client_id,
        agent_type="test",
        agent_model="test-model",
        agent_provider="test-provider",
        delegator_sub="test-delegator",  # Adding required delegator_sub
        launch_reason="test"
    )
    
    # Verify token is not revoked initially
    assert token_obj.is_revoked is False
    
    # Revoke the token via engine
    oauth_engine.revoke(token_obj.token_id)
    
    # Verify token is now revoked
    updated_token = IssuedToken.query.get(token_obj.token_id)
    assert updated_token.is_revoked is True
    
    # Clean up
    test_db.delete(token_obj)
    test_db.delete(agent)
    test_db.commit()

def test_introspect_token(test_db, oauth_engine):
    """Test token introspection using the refactored OAuth engine."""
    # Create an agent
    agent_name = "test_introspect_agent"
    agent, _ = Agent.create(agent_name=agent_name)
    
    # Create a token for introspection
    token_obj, access_token, _ = IssuedToken.create(
        client_id=agent.client_id,
        scope=["test:scope"],
        granted_tools=[],
        task_id="test-task",
        agent_instance_id=agent.client_id,
        agent_type="test",
        agent_model="test-model",
        agent_provider="test-provider",
        delegator_sub="test-delegator",  # Adding required delegator_sub
        launch_reason="test"
    )
    
    # Introspect the token via engine
    introspected_token = oauth_engine.introspect(access_token)
    
    # Verify introspection result
    assert introspected_token is not None
    assert introspected_token.token_id == token_obj.token_id
    assert introspected_token.client_id == agent.client_id
    
    # Clean up
    test_db.delete(token_obj)
    test_db.delete(agent)
    test_db.commit()
