"""Tests for Policy-Based Authorization for Delegated Tokens."""
import pytest
from unittest import mock
from agentictrust.core.oauth.token_handler import TokenHandler
from agentictrust.core.policy.opa_client import OPAClient

def test_delegation_policy_validation_success(test_db):
    """Test successful policy validation for delegated tokens."""
    with mock.patch("agentictrust.core.policy.opa_client.OPAClient.check_policy") as mock_check:
        mock_check.return_value = {
            "result": {
                "allow": True,
                "violations": []
            }
        }
        
        token_handler = TokenHandler()
        
        result = token_handler.validate_delegation_policy(
            user_id="user-123",
            agent_id="agent-456",
            scopes=["read:data"],
            constraints={"time_restrictions": {"start_hour": 9, "end_hour": 17}},
            purpose="testing"
        )
        
        assert result is True
        mock_check.assert_called_once()
        call_args = mock_check.call_args[0]
        assert call_args[0] == "human_delegation"
        assert "user_id" in call_args[1]
        assert "agent_id" in call_args[1]
        assert "scopes" in call_args[1]
        assert "constraints" in call_args[1]
        assert "purpose" in call_args[1]

def test_delegation_policy_validation_failure(test_db):
    """Test policy validation failure for delegated tokens."""
    with mock.patch("agentictrust.core.policy.opa_client.OPAClient.check_policy") as mock_check:
        mock_check.return_value = {
            "result": {
                "allow": False,
                "violations": ["Requested scope not allowed", "Time restriction violation"]
            }
        }
        
        token_handler = TokenHandler()
        
        result = token_handler.validate_delegation_policy(
            user_id="user-123",
            agent_id="agent-456",
            scopes=["admin:all"],  # Scope that would be denied
            constraints={},
            purpose="testing"
        )
        
        assert result is False
        mock_check.assert_called_once()
