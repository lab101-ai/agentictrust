"""Tests for Auth0 authentication flow."""
import pytest
from unittest import mock
from fastapi import HTTPException
from fastapi.testclient import TestClient
from agentictrust.main import app

client = TestClient(app)

def test_auth0_config(mock_auth0_client):
    """Test Auth0 configuration initialization."""
    from agentictrust.core.auth.auth0 import auth0_config
    
    assert "client_id" in auth0_config
    assert "client_secret" in auth0_config
    assert "api_base_url" in auth0_config
    assert "access_token_url" in auth0_config
    assert "authorize_url" in auth0_config
    assert "client_kwargs" in auth0_config
    assert "scope" in auth0_config["client_kwargs"]

@mock.patch("agentictrust.core.auth.auth0.OAuth")
def test_auth0_login_redirect(mock_oauth):
    """Test Auth0 login redirect."""
    mock_client = mock.MagicMock()
    mock_client.authorize_redirect.return_value = "https://auth0.com/authorize"
    mock_oauth.return_value.create_client.return_value = mock_client
    
    response = client.get("/api/login/auth0")
    
    assert response.status_code == 302
    assert "auth0.com" in response.headers["location"]
    mock_client.authorize_redirect.assert_called_once()

@mock.patch("agentictrust.core.auth.auth0.OAuth")
def test_auth0_callback(mock_oauth, mock_auth0_response):
    """Test Auth0 callback handling."""
    mock_client = mock.MagicMock()
    mock_client.authorize_access_token.return_value = {"userinfo": mock_auth0_response}
    mock_oauth.return_value.create_client.return_value = mock_client
    
    response = client.get("/api/login/auth0/callback?code=test_code&state=test_state")
    
    assert response.status_code == 302  # Redirect to frontend
    mock_client.authorize_access_token.assert_called_once()

@mock.patch("agentictrust.core.auth.auth0.requests.get")
def test_verify_auth0_token(mock_get, mock_auth0_response):
    """Test Auth0 token verification."""
    from agentictrust.core.auth.auth0 import verify_auth0_token
    
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = mock_auth0_response
    
    user_info = verify_auth0_token("test_token")
    
    assert user_info == mock_auth0_response
    mock_get.assert_called_with(
        "https://auth0.com/userinfo",
        headers={"Authorization": "Bearer test_token"}
    )

@mock.patch("agentictrust.core.auth.auth0.requests.get")
def test_verify_auth0_token_failure(mock_get):
    """Test Auth0 token verification failure."""
    from agentictrust.core.auth.auth0 import verify_auth0_token
    
    mock_get.return_value.status_code = 401
    
    with pytest.raises(HTTPException) as excinfo:
        verify_auth0_token("invalid_token")
    
    assert excinfo.value.status_code == 401
