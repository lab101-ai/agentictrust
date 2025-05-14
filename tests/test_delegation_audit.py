"""Tests for Enhanced Audit Logging for Delegation."""
import pytest
from datetime import datetime
from app.db.models.audit.delegation_audit import DelegationAuditLog

def test_create_delegation_audit_log(test_db, sample_user, sample_agent):
    """Test creating a delegation audit log."""
    audit_log = DelegationAuditLog.create(
        principal_id=sample_user.user_id,
        principal_type="user",
        delegate_id=sample_agent.client_id,
        delegate_type="agent",
        token_id="token-123",
        operation="delegate",
        status="success",
        scopes=["read:data"],
        purpose="testing",
        context={"ip_address": "127.0.0.1"}
    )
    
    assert audit_log.principal_id == sample_user.user_id
    assert audit_log.principal_type == "user"
    assert audit_log.delegate_id == sample_agent.client_id
    assert audit_log.delegate_type == "agent"
    assert audit_log.token_id == "token-123"
    assert audit_log.operation == "delegate"
    assert audit_log.status == "success"
    assert "read:data" in audit_log.scopes
    assert audit_log.purpose == "testing"
    assert audit_log.context["ip_address"] == "127.0.0.1"
    assert isinstance(audit_log.timestamp, datetime)
    
    test_db.delete(audit_log)
    test_db.commit()

def test_get_delegation_chain(test_db, sample_user, sample_agent):
    """Test retrieving a delegation chain."""
    parent_log = DelegationAuditLog.create(
        principal_id="user-parent",
        principal_type="user",
        delegate_id=sample_user.user_id,
        delegate_type="user",
        token_id="token-parent",
        operation="delegate",
        status="success",
        scopes=["read:data", "write:data"],
        purpose="parent delegation"
    )
    
    child_log = DelegationAuditLog.create(
        principal_id=sample_user.user_id,
        principal_type="user",
        delegate_id=sample_agent.client_id,
        delegate_type="agent",
        token_id="token-child",
        operation="delegate",
        status="success",
        scopes=["read:data"],
        purpose="child delegation",
        parent_token_id="token-parent"
    )
    
    chain = DelegationAuditLog.get_delegation_chain("token-child")
    
    assert len(chain) == 2
    assert chain[0].token_id == "token-parent"
    assert chain[1].token_id == "token-child"
    
    test_db.delete(child_log)
    test_db.delete(parent_log)
    test_db.commit()

def test_get_user_delegations(test_db, sample_user, sample_agent):
    """Test retrieving user delegations."""
    as_principal = DelegationAuditLog.create(
        principal_id=sample_user.user_id,
        principal_type="user",
        delegate_id=sample_agent.client_id,
        delegate_type="agent",
        token_id="token-principal",
        operation="delegate",
        status="success",
        scopes=["read:data"],
        purpose="as principal"
    )
    
    as_delegate = DelegationAuditLog.create(
        principal_id="other-user",
        principal_type="user",
        delegate_id=sample_user.user_id,
        delegate_type="user",
        token_id="token-delegate",
        operation="delegate",
        status="success",
        scopes=["admin:data"],
        purpose="as delegate"
    )
    
    activity = DelegationAuditLog.get_user_delegation_activity(sample_user.user_id)
    
    assert len(activity["delegations_as_principal"]) >= 1
    assert len(activity["delegations_as_delegate"]) >= 1
    assert any(d.token_id == "token-principal" for d in activity["delegations_as_principal"])
    assert any(d.token_id == "token-delegate" for d in activity["delegations_as_delegate"])
    
    test_db.delete(as_principal)
    test_db.delete(as_delegate)
    test_db.commit()
