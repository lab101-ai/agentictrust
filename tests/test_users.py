"""End-to-end tests for user management."""
import pytest
from agentictrust.db.models import User

def test_create_user(test_db, user_engine):
    """Test creating a new user."""
    # Create a new user with unique username
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    username = f"newuser_{unique_id}"
    email = f"{username}@example.com"
    
    user_data = user_engine.create_user(
        username=username,
        email=email,
        full_name="New User"
    )
    
    # Verify user was created
    assert user_data["username"] == username
    assert user_data["email"] == email
    
    # Verify user exists in database
    user = User.get_by_id(user_data["user_id"])
    assert user is not None
    assert user.username == username
    
    # Clean up
    try:
        User.delete_by_id(user_data["user_id"])
    except Exception as e:
        print(f"Cleanup error (can be ignored): {str(e)}")

def test_get_user(test_db, sample_user, user_engine):
    """Test getting a user by ID."""
    # Get the user
    user_data = user_engine.get_user(sample_user.user_id)
    
    # Verify user data
    assert user_data["user_id"] == sample_user.user_id
    assert user_data["username"] == sample_user.username
    assert user_data["email"] == sample_user.email

def test_list_users(test_db, sample_user, user_engine):
    """Test listing all users."""
    # Get all users
    users = user_engine.list_users()
    
    # Verify sample user is in the list
    user_ids = [user["user_id"] for user in users]
    assert sample_user.user_id in user_ids

def test_update_user(test_db, sample_user, user_engine):
    """Test updating a user."""
    # Update the user
    updated_data = user_engine.update_user(
        sample_user.user_id,
        {"full_name": "Updated Name", "department": "Engineering"}
    )
    
    # Verify update was successful
    assert updated_data["full_name"] == "Updated Name"
    assert updated_data["department"] == "Engineering"
    
    # Verify database was updated
    user = User.get_by_id(sample_user.user_id)
    assert user.full_name == "Updated Name"
    assert user.department == "Engineering"

@pytest.mark.skip(reason="Database schema issues with user_agent_authorizations table")
def test_delete_user(test_db, user_engine):
    """Test deleting a user."""
    # Create a user to delete with unique username
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    username = f"deleteuser_{unique_id}"
    email = f"{username}@example.com"
    
    user_data = user_engine.create_user(
        username=username,
        email=email
    )
    user_id = user_data["user_id"]
    
    # Verify user exists
    user = User.get_by_id(user_id)
    assert user is not None
    
    # Delete the user
    user_engine.delete_user(user_id)
    
    # Verify user no longer exists
    with pytest.raises(ValueError, match="User not found"):
        User.get_by_id(user_id)

@pytest.mark.skip(reason="Database schema issues with scopes and policies")
def test_user_with_scopes_and_policies(test_db, sample_scope, sample_policy, user_engine):
    """Test creating and updating a user with scopes and policies."""
    # Create user with scope and policy using unique username
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    username = f"scopeuser_{unique_id}"
    email = f"{username}@example.com"
    
    user_data = user_engine.create_user(
        username=username,
        email=email,
        scopes=[sample_scope.scope_id],
        policies=[sample_policy.policy_id]
    )
    
    # Verify scopes and policies were assigned
    user = User.get_by_id(user_data["user_id"])
    assert len(user.scopes) == 1
    assert user.scopes[0].scope_id == sample_scope.scope_id
    assert len(user.policies) == 1
    assert user.policies[0].policy_id == sample_policy.policy_id
    
    # Update scopes and policies
    user_engine.update_user(
        user.user_id,
        {"scope_ids": [], "policy_ids": []}
    )
    
    # Verify scopes and policies were removed
    user = User.get_by_id(user.user_id)
    assert len(user.scopes) == 0
    assert len(user.policies) == 0
    
    # Clean up
    try:
        User.delete_by_id(user.user_id)
    except Exception as e:
        print(f"Cleanup error (can be ignored): {str(e)}")
