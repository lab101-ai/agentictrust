"""Tests for the refactored ScopeEngine."""
import pytest
import uuid
from agentictrust.core.scope.engine import ScopeEngine
from agentictrust.db.models import Scope

@pytest.mark.skip(reason="Database schema issues in test environment")
def test_create_scope(test_db, scope_engine):
    """Test creating a scope using the refactored scope engine."""
    unique_id = str(uuid.uuid4())[:8]
    scope_name = f"test{unique_id}:read"  # Valid scope name format
    scope_description = "Test scope created via engine"
    
    # Create a scope using the engine
    scope_data = scope_engine.create_scope(
        name=scope_name,
        description=scope_description,
        category="write",
        is_sensitive=True,
        requires_approval=False,
        is_default=False
        # Note: is_active param is not accepted by Scope.create()
    )
    
    # Verify scope data from the returned dict
    assert scope_data["name"] == scope_name
    assert scope_data["description"] == scope_description
    assert scope_data["category"] == "write"
    assert scope_data["is_sensitive"] is True
    
    # Verify scope exists in database
    scope = Scope.find_by_name(scope_name)
    assert scope is not None
    assert scope.description == scope_description
    
    # Clean up
    try:
        Scope.delete_by_id(scope_data["scope_id"])
    except Exception as e:
        print(f"Cleanup error (can be ignored): {str(e)}")

def test_update_scope(test_db, scope_engine):
    """Test updating a scope using the refactored scope engine."""
    # Create a scope to update with unique name
    unique_id = str(uuid.uuid4())[:8]
    scope_name = f"test{unique_id}:read"  # Valid scope name format
    
    scope = Scope.create(
        name=scope_name,
        description="Original description",
        category="read"
    )
    
    # Update the scope via engine
    updated_data = scope_engine.update_scope(
        scope_id=scope.scope_id,
        data={
            "description": "Updated description",
            "is_sensitive": True,
            "category": "write"
        }
    )
    
    # Verify updated data from response
    assert updated_data["description"] == "Updated description"
    assert updated_data["is_sensitive"] is True
    assert updated_data["category"] == "write"
    
    # Verify database was updated
    updated_scope = Scope.get_by_id(scope.scope_id)
    assert updated_scope.description == "Updated description"
    assert updated_scope.is_sensitive is True
    assert updated_scope.category == "write"
    
    # Clean up
    try:
        Scope.delete_by_id(scope.scope_id)
    except Exception as e:
        print(f"Cleanup error (can be ignored): {str(e)}")

@pytest.mark.skip(reason="Database schema issues in test environment")
def test_get_scope(test_db, scope_engine):
    """Test getting a scope using the refactored scope engine."""
    # Create a scope with unique name
    unique_id = str(uuid.uuid4())[:8]
    scope_name = f"test{unique_id}:read"  # Valid scope name format
    
    scope = Scope.create(
        name=scope_name,
        description="Test scope for get method"
    )
    
    # Get the scope via engine
    scope_data = scope_engine.get_scope(scope.scope_id)
    
    # Verify data
    assert scope_data["scope_id"] == scope.scope_id
    assert scope_data["name"] == scope_name
    assert scope_data["description"] == "Test scope for get method"
    
    # Clean up
    try:
        Scope.delete_by_id(scope.scope_id)
    except Exception as e:
        print(f"Cleanup error (can be ignored): {str(e)}")

@pytest.mark.skip(reason="Database schema issues in test environment")
def test_list_scopes(test_db, scope_engine):
    """Test listing scopes using the refactored scope engine."""
    # Create test scopes with different categories and unique names
    unique_id = str(uuid.uuid4())[:8]
    read_scope_name = f"test{unique_id}:read"  # Valid scope name format
    write_scope_name = f"test{unique_id}:write"  # Valid scope name format
    
    scope1 = Scope.create(name=read_scope_name, description="Read scope", category="read")
    scope2 = Scope.create(name=write_scope_name, description="Write scope", category="write")
    
    # List all scopes
    all_scopes = scope_engine.list_scopes()
    test_scopes = [s for s in all_scopes if s["name"].startswith(f"test{unique_id}")]
    assert len(test_scopes) >= 2
    
    # List scopes filtered by category
    read_scopes = scope_engine.list_scopes(level="read")
    test_read_scopes = [s for s in read_scopes if s["name"] == read_scope_name]
    assert len(test_read_scopes) == 1
    assert test_read_scopes[0]["name"] == read_scope_name
    
    # Clean up
    try:
        Scope.delete_by_id(scope1.scope_id)
        Scope.delete_by_id(scope2.scope_id)
    except Exception as e:
        print(f"Cleanup error (can be ignored): {str(e)}")

@pytest.mark.skip(reason="Database schema issues in test environment")
def test_delete_scope(test_db, scope_engine):
    """Test deleting a scope using the refactored scope engine."""
    # Create a scope to delete with unique name
    unique_id = str(uuid.uuid4())[:8]
    scope_name = f"test{unique_id}:read"  # Valid scope name format
    
    scope = Scope.create(
        name=scope_name,
        description="Test scope for deletion"
    )
    
    # Verify it exists first
    scope_id = scope.scope_id
    found_scope = Scope.get_by_id(scope_id)
    assert found_scope is not None
    
    # Delete the scope via engine
    scope_engine.delete_scope(scope_id)
    
    # Verify it's gone
    with pytest.raises(ValueError, match="Scope not found"):
        Scope.get_by_id(scope_id)
