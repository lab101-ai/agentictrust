"""Tests for Auth0 User model integration."""
import pytest
import json
from app.db.models import User

def test_user_with_auth0_fields(test_db):
    """Test creating a user with Auth0-specific fields."""
    auth0_id = "auth0|123456"
    auth0_metadata = {"roles": ["user"], "app_metadata": {"plan": "free"}}
    
    user = User.create(
        username="auth0user",
        email="auth0user@example.com",
        auth0_id=auth0_id,
        auth0_metadata=json.dumps(auth0_metadata),
        social_provider="google",
        social_provider_id="google|12345",
        mfa_enabled=True,
        mfa_type="totp"
    )
    
    assert user.auth0_id == auth0_id
    assert json.loads(user.auth0_metadata) == auth0_metadata
    assert user.social_provider == "google"
    assert user.mfa_enabled is True
    assert user.mfa_type == "totp"
    
    user.set_auth0_metadata({"updated": True})
    assert user.get_auth0_metadata() == {"updated": True}
    
    User.delete_by_id(user.user_id)

def test_user_auth0_metadata_methods(test_db, sample_auth0_user):
    """Test Auth0 metadata getter and setter methods."""
    new_metadata = {"roles": ["admin"], "permissions": ["read:all"]}
    sample_auth0_user.set_auth0_metadata(new_metadata)
    
    assert sample_auth0_user.get_auth0_metadata() == new_metadata
    
    sample_auth0_user.auth0_metadata = "invalid-json"
    assert sample_auth0_user.get_auth0_metadata() == {}
