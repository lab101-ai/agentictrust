"""Tests for Human-to-Agent Token Delegation."""
import pytest
from unittest import mock
import uuid
from agentictrust.core.oauth.engine import OAuthEngine
from tests.conftest import MockUserAgentAuthorization
from tests.mock_issued_token import MockIssuedToken
from agentictrust.utils.logger import logger

def direct_mock_verify_token(token_str, allow_clock_skew=True, max_clock_skew_seconds=86400):
    """Direct mock implementation that always returns a valid token."""
    logger.debug(f"Direct mock verify_token called with token: {token_str}")
    
    mock_token = MockIssuedToken(
        token_id=str(uuid.uuid4()),
        client_id="mock_client",
        scope="read:data write:data",
        delegator_sub="mock_user_id"
    )
    return mock_token

@pytest.mark.skip_cleanup
def test_delegate_token_from_human_to_agent(test_db, sample_user, sample_agent, oauth_engine, sample_user_agent_authorization):
    """Test delegating a token from a human user to an agent."""
    if not hasattr(MockUserAgentAuthorization, '_authorizations'):
        MockUserAgentAuthorization._authorizations = {}
    
    MockUserAgentAuthorization._authorizations[sample_user_agent_authorization.authorization_id] = sample_user_agent_authorization
    
    user_token_obj, user_access_token, _ = MockIssuedToken.create(
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
    
    delegated_token_obj, delegated_access_token, delegated_refresh_token = MockIssuedToken.create(
        client_id=sample_agent.client_id,
        scope=["read:data"],
        task_id="delegated-task",
        delegator_sub=sample_user.user_id,
        agent_instance_id="agent-instance-id"
    )
    
    with mock.patch.object(OAuthEngine, 'process_human_delegation', autospec=True) as mock_process:
        mock_process.return_value = {
            "access_token": delegated_access_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": delegated_refresh_token,
            "scope": "read:data",
            "task_id": "delegated-task"
        }
        
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
    assert delegated_token["access_token"] == delegated_access_token
    
    try:
        MockIssuedToken.delete_by_id(user_token_obj.token_id)
        MockIssuedToken.delete_by_id(delegated_token_obj.token_id)
    except Exception as e:
        logger.warning(f"Error during cleanup: {str(e)}")

@pytest.mark.skip_cleanup
def test_delegate_token_unauthorized_agent(test_db, sample_user, sample_agent, oauth_engine):
    """Test delegating a token to an unauthorized agent."""
    if not hasattr(MockUserAgentAuthorization, '_authorizations'):
        MockUserAgentAuthorization._authorizations = {}
    
    user_token_obj, user_access_token, _ = MockIssuedToken.create(
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
    
    with mock.patch.object(OAuthEngine, 'process_human_delegation', autospec=True) as mock_process:
        mock_process.side_effect = Exception("Invalid delegator token")
        
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
        
        error_msg = str(excinfo.value).lower()
        assert "invalid delegator token" in error_msg
    
    try:
        MockIssuedToken.delete_by_id(user_token_obj.token_id)
    except Exception as e:
        logger.warning(f"Error during cleanup: {str(e)}")
