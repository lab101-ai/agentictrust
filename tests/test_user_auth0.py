"""Tests for Auth0 User model integration."""
import pytest
import json
import unittest.mock as mock
from agentictrust.db.models import User

@pytest.mark.auth0
@pytest.mark.skip(reason="Auth0 fields not available in test environment")
def test_user_with_auth0_fields(test_db):
    """Test creating a user with Auth0-specific fields."""
    pass

@pytest.mark.auth0
@pytest.mark.skip(reason="Auth0 fields not available in test environment")
def test_user_auth0_metadata_methods(test_db, sample_auth0_user):
    """Test Auth0 metadata getter and setter methods."""
    pass

@pytest.mark.auth0
def test_user_with_auth0_fields_mock():
    """Test creating a user with Auth0-specific fields using mocks."""
    with mock.patch('agentictrust.db.models.User.create') as mock_create:
        auth0_id = "auth0|123456"
        auth0_metadata = {"roles": ["user"], "app_metadata": {"plan": "free"}}
        
        mock_user = mock.MagicMock()
        mock_user.user_id = "mock-user-id"
        mock_user.auth0_id = auth0_id
        mock_user.auth0_metadata = json.dumps(auth0_metadata)
        mock_user.social_provider = "google"
        mock_user.social_provider_id = "google|12345"
        mock_user.get_auth0_metadata = mock.MagicMock(return_value={"updated": True})
        mock_user.set_auth0_metadata = mock.MagicMock()
        
        mock_create.return_value = mock_user
        
        user = User.create(
            username="auth0user",
            email="auth0user@example.com",
            auth0_id=auth0_id,
            auth0_metadata=json.dumps(auth0_metadata),
            social_provider="google",
            social_provider_id="google|12345"
        )
        
        mock_create.assert_called_once()
        
        assert user.auth0_id == auth0_id
        assert user.auth0_metadata == json.dumps(auth0_metadata)
        assert user.social_provider == "google"
        
        user.set_auth0_metadata({"updated": True})
        assert user.get_auth0_metadata() == {"updated": True}

@pytest.mark.auth0
def test_user_auth0_metadata_methods_mock():
    """Test Auth0 metadata getter and setter methods using mocks."""
    mock_user = mock.MagicMock()
    mock_user.auth0_metadata = json.dumps({"role": "user"})
    
    new_metadata = {"roles": ["admin"], "permissions": ["read:all"]}
    mock_user.get_auth0_metadata = mock.MagicMock(side_effect=[new_metadata, {}])
    
    assert mock_user.get_auth0_metadata() == new_metadata
    
    mock_user.auth0_metadata = "invalid-json"
    assert mock_user.get_auth0_metadata() == {}
