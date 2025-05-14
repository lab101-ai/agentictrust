"""Tests for Multi-Factor Authentication for Critical Agent Operations."""
import pytest
from unittest import mock
import pyotp
from app.core.auth.mfa import MFAManager, MFAChallenge

def test_mfa_setup(test_db, sample_auth0_user):
    """Test setting up MFA for a user."""
    mfa_manager = MFAManager()
    
    setup_result = mfa_manager.setup_mfa(sample_auth0_user)
    
    assert "secret" in setup_result
    assert "qr_code" in setup_result
    assert "uri" in setup_result
    
    assert sample_auth0_user.mfa_enabled is True
    assert sample_auth0_user.mfa_type == "totp"
    assert hasattr(sample_auth0_user, "mfa_secret")

def test_verify_mfa_code(test_db, sample_auth0_user):
    """Test verifying an MFA code."""
    mfa_manager = MFAManager()
    
    if not sample_auth0_user.mfa_enabled:
        mfa_manager.setup_mfa(sample_auth0_user)
    
    with mock.patch("pyotp.TOTP.verify") as mock_verify:
        mock_verify.return_value = True
        
        result = mfa_manager.verify_mfa(sample_auth0_user, "123456")
        
        assert result is True
        mock_verify.assert_called_with("123456")


def test_create_mfa_challenge(test_db, sample_auth0_user):
    """Test creating an MFA challenge."""
    mfa_manager = MFAManager()
    
    challenge = mfa_manager.create_challenge(
        user_id=sample_auth0_user.user_id,
        operation_type="token_delegation"
    )
    
    assert challenge is not None
    assert challenge.user_id == sample_auth0_user.user_id
    assert challenge.operation_type == "token_delegation"
    assert challenge.is_verified is False
    assert challenge.expires_at is not None
    
    test_db.delete(challenge)
    test_db.commit()

def test_verify_mfa_challenge(test_db, sample_auth0_user):
    """Test verifying an MFA challenge."""
    mfa_manager = MFAManager()
    
    challenge = mfa_manager.create_challenge(
        user_id=sample_auth0_user.user_id,
        operation_type="token_delegation"
    )
    
    with mock.patch("pyotp.TOTP.verify") as mock_verify:
        mock_verify.return_value = True
        
        result = mfa_manager.verify_challenge(
            user_id=sample_auth0_user.user_id,
            challenge_id=challenge.challenge_id,
            code="123456"
        )
        
        assert result is True
        
        updated_challenge = MFAChallenge.query.get(challenge.challenge_id)
        assert updated_challenge.is_verified is True
    
    test_db.delete(challenge)
    test_db.commit()
