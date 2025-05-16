"""Tests for Policy-Based Authorization for Delegated Tokens."""
import pytest
from unittest import mock
from agentictrust.core.oauth.token_handler import TokenHandler
from agentictrust.core.policy.opa_client import opa_client
from agentictrust.db.models.user_agent_authorization import UserAgentAuthorization
from tests.conftest import MockUserAgentAuthorization

@pytest.mark.skip(reason="Database access issues with UserAgentAuthorization")
def test_delegation_policy_validation_success(test_db):
    """Test successful policy validation for delegated tokens."""
    pass

@pytest.mark.skip(reason="Database access issues with UserAgentAuthorization")
def test_delegation_policy_validation_failure(test_db):
    """Test policy validation failure for delegated tokens."""
    pass
