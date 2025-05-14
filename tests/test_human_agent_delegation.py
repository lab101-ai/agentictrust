"""Tests for Human-to-Agent Token Delegation."""
import pytest
from unittest import mock
from agentictrust.core.oauth.engine import OAuthEngine
from agentictrust.db.models import IssuedToken

def test_delegate_token_from_human_to_agent(test_db, sample_user, sample_agent, oauth_engine):
    """Test delegating a token from a human user to an agent."""
    user_token_obj, user_access_token, _ = IssuedToken.create(
        client_id="human_client",
        scope=["read:data", "write:data"],
        granted_tools=[],
        task_id="user-task",
        agent_instance_id="human_client",
        agent_type="human",
        agent_model="human",
        agent_provider="direct",
        delegator_sub=sample_user.user_id,
        launch_reason="test"
    )
    
    with mock.patch("agentictrust.db.models.user_agent_authorization.UserAgentAuthorization.check_authorization") as mock_check:
        mock_check.return_value = True
        
        delegated_token = oauth_engine.delegate_token(
            client_id=sample_agent.client_id,
            delegation_type="human_to_agent",
            delegator_token=user_access_token,
            scope=["read:data"],
            task_description="Test delegation",
            task_id="delegated-task",
            purpose="testing"
        )
    
    assert delegated_token is not None
    assert "access_token" in delegated_token
    assert "token_type" in delegated_token
    assert "expires_in" in delegated_token
    
    delegated_token_obj = IssuedToken.query.filter_by(task_id="delegated-task").first()
    assert delegated_token_obj is not None
    assert delegated_token_obj.client_id == sample_agent.client_id
    assert delegated_token_obj.delegator_sub == sample_user.user_id
    assert "read:data" in delegated_token_obj.scope
    assert len(delegated_token_obj.scope) == 1  # Only requested scope, not all user scopes
    
    test_db.delete(user_token_obj)
    test_db.delete(delegated_token_obj)
    test_db.commit()

def test_delegate_token_unauthorized_agent(test_db, sample_user, sample_agent, oauth_engine):
    """Test delegating a token to an unauthorized agent."""
    user_token_obj, user_access_token, _ = IssuedToken.create(
        client_id="human_client",
        scope=["read:data", "write:data"],
        granted_tools=[],
        task_id="user-task",
        agent_instance_id="human_client",
        agent_type="human",
        agent_model="human",
        agent_provider="direct",
        delegator_sub=sample_user.user_id,
        launch_reason="test"
    )
    
    with mock.patch("agentictrust.db.models.user_agent_authorization.UserAgentAuthorization.check_authorization") as mock_check:
        mock_check.return_value = False
        
        with pytest.raises(Exception) as excinfo:
            oauth_engine.delegate_token(
                client_id=sample_agent.client_id,
                delegation_type="human_to_agent",
                delegator_token=user_access_token,
                scope=["read:data"],
                task_description="Test delegation",
                task_id="delegated-task-fail",
                purpose="testing"
            )
        
        assert "not authorized" in str(excinfo.value).lower()
    
    test_db.delete(user_token_obj)
    test_db.commit()
