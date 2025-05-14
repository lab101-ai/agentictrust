"""Tests for Role-Based Access Control for Agents."""
import pytest
from unittest import mock
from app.db.models.role import Role
from app.db.models.permission import Permission

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
    test_db.delete(permission)
    test_db.delete(role)
    test_db.commit()

def test_assign_role_to_agent(test_db, sample_agent):
    """Test assigning a role to an agent."""
    role = Role.create(
        name="agent_role",
        description="Role for agent"
    )
    
    sample_agent.roles.append(role)
    test_db.commit()
    
    agent = sample_agent.__class__.get_by_id(sample_agent.client_id)
    assert len(agent.roles) == 1
    assert agent.roles[0].name == "agent_role"
    
    agent.roles.remove(role)
    test_db.delete(role)
    test_db.commit()

def test_rbac_policy_validation(test_db):
    """Test RBAC policy validation."""
    with mock.patch("app.core.policy.opa_client.OPAClient.check_policy") as mock_check:
        mock_check.return_value = {
            "result": {
                "allow": True,
                "violations": []
            }
        }
        
        from app.routers.oauth import verify_with_rbac
        
        result = verify_with_rbac(
            token="test-token",
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
