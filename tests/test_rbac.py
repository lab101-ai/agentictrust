"""Tests for Role-Based Access Control for Agents."""
import pytest
from unittest import mock
from agentictrust.db.models.role import Role
from agentictrust.db.models.permission import Permission

def test_create_role_and_permission(test_db):
    """Test creating a role and permission."""
    permission = Permission.create(
        name="read_user_data",
        resource="user_data",
        action="read",
        description="Permission to read user data"
    )

    role = Role.create(
        name="data_analyst",
        description="Role for data analysts"
    )

    role.add_permission(permission)

    role_permissions = role.get_permissions()
    assert len(role_permissions) == 1
    assert role_permissions[0].permission_id == permission.permission_id

    role.remove_permission(permission)

@pytest.mark.skip(reason="Requires roles table which doesn't exist in test database")
def test_assign_role_to_agent(test_db, sample_agent):
    """Test assigning a role to an agent."""
    role = Role.create(
        name="agent_role",
        description="Role for agent"
    )
    
    if not hasattr(sample_agent, 'roles'):
        sample_agent.roles = []
    sample_agent.roles.append(role)
    
    assert len(sample_agent.roles) == 1
    assert sample_agent.roles[0].name == "agent_role"
    
    sample_agent.roles.remove(role)

def test_rbac_policy_validation(test_db):
    """Test RBAC policy validation."""
    from tests.mock_issued_token import MockIssuedToken
    
    token_obj, access_token, _ = MockIssuedToken.create(
        client_id="test-client",
        scope="read:data write:data",
        task_id="test-task"
    )
    
    with mock.patch("agentictrust.core.policy.opa_client.OPAClient.check_policy") as mock_check, \
         mock.patch("agentictrust.core.oauth.utils.verify_token") as mock_verify:
        
        mock_check.return_value = {
            "result": {
                "allow": True,
                "violations": []
            }
        }
        mock_verify.return_value = token_obj
        
        from agentictrust.routers.oauth import verify_with_rbac
        
        result = verify_with_rbac(
            token=access_token,
            resource="user_data",
            action="read",
            roles=["data_analyst"],
            permissions=["read_user_data"]
        )
        
        assert result["allowed"] is True
        mock_check.assert_called_once()
        call_args = mock_check.call_args[0]
        assert call_args[0] == "rbac"
        assert "roles" in call_args[1]
        assert "permissions" in call_args[1]
        assert "resource" in call_args[1]
        assert "action" in call_args[1]
