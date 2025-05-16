"""Tests for AgenticTrust SDK client."""
import pytest
from unittest import mock
import requests
from sdk.agentictrust.client import AgenticTrustClient

def test_client_initialization():
    """Test initializing the SDK client."""
    client = AgenticTrustClient(base_url="http://localhost:8000", api_key="test-key")
    
    assert client.base_url == "http://localhost:8000"
    assert client.api_key == "test-key"
    assert client.session.headers["X-API-Key"] == "test-key"


@mock.patch("requests.Session.post")
def test_delegate_token(mock_post):
    """Test delegating a token using the SDK client."""
    mock_response = mock.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "delegated-token",
        "token_type": "bearer",
        "expires_in": 3600
    }
    mock_post.return_value = mock_response
    
    client = AgenticTrustClient(base_url="http://localhost:8000")
    
    result = client.delegate_token(
        client_id="agent-123",
        delegator_token="user-token",
        scopes=["read:data"],
        task_description="Test delegation",
        task_id="task-123",
        purpose="testing"
    )
    
    assert result["access_token"] == "delegated-token"
    assert result["token_type"] == "bearer"
    assert result["expires_in"] == 3600
    
    mock_post.assert_called_with(
        "http://localhost:8000/api/oauth/delegate",
        json={
            "client_id": "agent-123",
            "delegation_type": "human_to_agent",
            "delegator_token": "user-token",
            "scope": ["read:data"],
            "task_description": "Test delegation",
            "task_id": "task-123",
            "parent_task_id": None,
            "purpose": "testing",
            "constraints": None,
            "agent_instance_id": None
        }
    )



@mock.patch("requests.Session.get")
def test_get_delegation_chain(mock_get):
    """Test getting a delegation chain."""
    mock_response = mock.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "chain": [
            {
                "token_id": "token-parent",
                "principal_id": "user-123",
                "delegate_id": "agent-456"
            },
            {
                "token_id": "token-child",
                "principal_id": "agent-456",
                "delegate_id": "agent-789"
            }
        ]
    }
    mock_get.return_value = mock_response
    
    client = AgenticTrustClient(base_url="http://localhost:8000")
    
    result = client.get_delegation_chain("token-child")
    
    assert "chain" in result
    assert len(result["chain"]) == 2
    assert result["chain"][0]["token_id"] == "token-parent"
    assert result["chain"][1]["token_id"] == "token-child"
    
    mock_get.assert_called_with(
        "http://localhost:8000/api/audit/delegation/token-child/chain"
    )

@mock.patch("requests.Session.post")
def test_verify_with_rbac(mock_post):
    """Test verifying a token with RBAC."""
    mock_response = mock.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "allowed": True,
        "token_info": {
            "client_id": "agent-123",
            "scope": ["read:data"]
        }
    }
    mock_post.return_value = mock_response
    
    client = AgenticTrustClient(base_url="http://localhost:8000")
    client.set_token("test-token")
    
    result = client.verify_with_rbac(
        token="test-token",
        resource="user_data",
        action="read"
    )
    
    assert result["allowed"] is True
    assert "token_info" in result
    
    mock_post.assert_called_with(
        "http://localhost:8000/api/oauth/verify_with_rbac",
        json={
            "resource": "user_data",
            "action": "read"
        },
        headers={"Authorization": "Bearer test-token"}
    )
