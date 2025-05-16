"""Integration tests for complete Auth0 flow."""
import pytest
from unittest import mock
from fastapi.testclient import TestClient
from agentictrust.main import app

client = TestClient(app)

@pytest.mark.integration
def test_complete_auth0_flow(test_db, mock_auth0_response, sample_agent):
    """Test the complete Auth0 authentication and delegation flow."""
    with mock.patch("agentictrust.core.auth.auth0.OAuth") as mock_oauth:
        mock_client = mock.MagicMock()
        mock_client.authorize_redirect.return_value = "https://auth0.com/authorize"
        mock_client.authorize_access_token.return_value = {"userinfo": mock_auth0_response}
        mock_oauth.return_value.create_client.return_value = mock_client
        
        login_response = client.get("/api/login/auth0")
        assert login_response.status_code == 302
        
        callback_response = client.get("/api/login/auth0/callback?code=test_code&state=test_state")
        assert callback_response.status_code == 302
    
    with mock.patch("agentictrust.core.auth.auth0.verify_auth0_token") as mock_verify:
        mock_verify.return_value = mock_auth0_response
        
        exchange_response = client.post(
            "/api/users/auth0/token",
            json={"auth0_token": "auth0-token"}
        )
        
        assert exchange_response.status_code == 200
        assert "access_token" in exchange_response.json()
        user_token = exchange_response.json()["access_token"]
    
    from agentictrust.db.models.user import User
    user = User.query.filter_by(auth0_id=mock_auth0_response["sub"]).first()
    
    auth_response = client.post(
        f"/api/users/{user.user_id}/authorizations",
        json={
            "user_id": user.user_id,
            "agent_id": sample_agent.client_id,
            "scopes": ["read:data", "write:data"],
            "constraints": {"time_restrictions": {"start_hour": 9, "end_hour": 17}},
            "ttl_days": 30
        },
        headers={"Authorization": f"Bearer {user_token}"}
    )
    
    assert auth_response.status_code == 200
    assert "authorization_id" in auth_response.json()
    
    with mock.patch("agentictrust.core.policy.opa_client.OPAClient.check_policy") as mock_check:
        mock_check.return_value = {
            "result": {
                "allow": True,
                "violations": []
            }
        }
        
        delegate_response = client.post(
            "/api/oauth/delegate",
            json={
                "client_id": sample_agent.client_id,
                "delegation_type": "human_to_agent",
                "delegator_token": user_token,
                "scope": ["read:data"],
                "task_description": "Integration test",
                "task_id": "integration-task",
                "purpose": "testing"
            }
        )
        
        assert delegate_response.status_code == 200
        assert "access_token" in delegate_response.json()
        delegated_token = delegate_response.json()["access_token"]
    
    resource_response = client.get(
        "/api/protected-resource",
        headers={"Authorization": f"Bearer {delegated_token}"}
    )
    
    assert resource_response.status_code != 401
    
    audit_response = client.get(
        f"/api/audit/delegation/user/{user.user_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    
    assert audit_response.status_code == 200
    assert "delegations_as_principal" in audit_response.json()
    assert len(audit_response.json()["delegations_as_principal"]) >= 1
    
    from agentictrust.db.models.user_agent_authorization import UserAgentAuthorization
    authorizations = UserAgentAuthorization.query.filter_by(user_id=user.user_id).all()
    for auth in authorizations:
        test_db.delete(auth)
    
    test_db.delete(user)
    test_db.commit()
