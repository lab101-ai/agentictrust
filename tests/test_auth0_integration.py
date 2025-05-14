"""Integration tests for complete Auth0 flow."""
import pytest
from unittest import mock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.mark.integration
def test_complete_auth0_flow(test_db, mock_auth0_response, sample_agent):
    """Test the complete Auth0 authentication and delegation flow."""
    with mock.patch("app.core.auth.auth0.OAuth") as mock_oauth:
        mock_client = mock.MagicMock()
        mock_client.authorize_redirect.return_value = "https://auth0.com/authorize"
        mock_client.authorize_access_token.return_value = {"userinfo": mock_auth0_response}
        mock_oauth.return_value.create_client.return_value = mock_client
        
        login_response = client.get("/api/login/auth0")
        assert login_response.status_code == 302
        
        callback_response = client.get("/api/login/auth0/callback?code=test_code&state=test_state")
        assert callback_response.status_code == 302
    
    with mock.patch("app.core.auth.auth0.verify_auth0_token") as mock_verify:
        mock_verify.return_value = mock_auth0_response
        
        exchange_response = client.post(
            "/api/users/auth0/token",
            json={"auth0_token": "auth0-token"}
        )
        
        assert exchange_response.status_code == 200
        assert "access_token" in exchange_response.json()
        user_token = exchange_response.json()["access_token"]
    
    from app.db.models.user import User
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
    
    with mock.patch("app.core.policy.opa_client.OPAClient.check_policy") as mock_check:
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
    
    from app.db.models.user_agent_authorization import UserAgentAuthorization
    authorizations = UserAgentAuthorization.query.filter_by(user_id=user.user_id).all()
    for auth in authorizations:
        test_db.delete(auth)
    
    test_db.delete(user)
    test_db.commit()

@pytest.mark.integration
def test_auth0_mfa_delegation_flow(test_db, mock_auth0_response, sample_agent, sample_auth0_user):
    """Test the Auth0 authentication with MFA for delegation."""
    with mock.patch("app.core.auth.auth0.verify_auth0_token") as mock_verify:
        mock_verify.return_value = mock_auth0_response
        
        exchange_response = client.post(
            "/api/users/auth0/token",
            json={"auth0_token": "auth0-token"}
        )
        
        user_token = exchange_response.json()["access_token"]
    
    auth_response = client.post(
        f"/api/users/{sample_auth0_user.user_id}/authorizations",
        json={
            "user_id": sample_auth0_user.user_id,
            "agent_id": sample_agent.client_id,
            "scopes": ["read:data", "write:data"],
            "constraints": {"time_restrictions": {"start_hour": 9, "end_hour": 17}},
            "ttl_days": 30
        },
        headers={"Authorization": f"Bearer {user_token}"}
    )
    
    with mock.patch("app.core.auth.mfa.MFAManager.create_challenge") as mock_create:
        mock_create.return_value = mock.MagicMock(
            challenge_id="challenge-123",
            user_id=sample_auth0_user.user_id,
            operation_type="token_delegation",
            is_verified=False
        )
        
        challenge_response = client.post(
            f"/api/mfa/users/{sample_auth0_user.user_id}/challenge",
            params={"operation_type": "token_delegation"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert challenge_response.status_code == 200
        assert "challenge_id" in challenge_response.json()
        challenge_id = challenge_response.json()["challenge_id"]
    
    with mock.patch("app.core.auth.mfa.MFAManager.verify_challenge") as mock_verify:
        mock_verify.return_value = True
        
        verify_response = client.post(
            f"/api/mfa/users/{sample_auth0_user.user_id}/challenge/verify",
            json={
                "challenge_id": challenge_id,
                "code": "123456"
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert verify_response.status_code == 200
        assert verify_response.json()["verified"] is True
    
    with mock.patch("app.core.policy.opa_client.OPAClient.check_policy") as mock_check:
        mock_check.return_value = {
            "result": {
                "allow": True,
                "violations": []
            }
        }
        
        delegate_response = client.post(
            "/api/oauth/delegate/mfa",
            json={
                "client_id": sample_agent.client_id,
                "delegation_type": "human_to_agent",
                "delegator_token": user_token,
                "scope": ["read:data", "write:data"],
                "task_description": "MFA integration test",
                "task_id": "mfa-integration-task",
                "purpose": "testing with MFA"
            },
            params={
                "mfa_challenge_id": challenge_id,
                "mfa_code": "123456"
            }
        )
        
        assert delegate_response.status_code == 200
        assert "access_token" in delegate_response.json()
    
    from app.db.models.user_agent_authorization import UserAgentAuthorization
    authorizations = UserAgentAuthorization.query.filter_by(user_id=sample_auth0_user.user_id).all()
    for auth in authorizations:
        test_db.delete(auth)
