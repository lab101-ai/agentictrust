"""Centralised OAuth business logic used by routers and services."""
from __future__ import annotations

import secrets
import uuid
from typing import List, Dict, Any, Optional, Tuple, cast
from datetime import timedelta

from app.db import db_session
from app.db.models import Agent, IssuedToken
from app.db.models.authorization_code import AuthorizationCode
from app.db.models.audit.policy_audit import PolicyAuditLog
from app.db.models.audit.scope_audit import ScopeAuditLog
from app.db.models.audit.token_audit import TokenAuditLog
from app.db.models.audit.delegation_audit import DelegationAuditLog

from app.core.oauth.utils import verify_token, pkce_verify
from app.schemas.oauth import TokenRequestClientCredentials, LaunchReason

class OAuthEngine:
    """Facade for issuing & validating tokens.

    Routers call this instead of directly touching models so the policy &
    scope engines can be injected later.
    """

    # ------------------------------------------------------------------
    # Authorization Code (PKCE) flow helpers
    # ------------------------------------------------------------------
    def create_authorization_code(
        self,
        *,
        client_id: str,
        redirect_uri: str,
        scope: str | List[str] | None = None,
        code_challenge: str,
        code_challenge_method: str = "S256",
        state: Optional[str] = None,
        lifetime_seconds: int = 600,
    ) -> Tuple[str, str]:
        """Generate plaintext code & persist row. Returns (code, state)."""
        plaintext_code = secrets.token_urlsafe(32)
        AuthorizationCode.create(
            code_plain=plaintext_code,
            client_id=client_id,
            scope=scope or "",
            redirect_uri=redirect_uri,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            lifetime_seconds=lifetime_seconds,
        )
        return plaintext_code, state

    def exchange_code_for_token(
        self,
        *,
        client_id: str,
        code_plain: str,
        redirect_uri: str,
        code_verifier: str,
        access_expires_in: Optional[timedelta] = None,
        launch_reason: str = "user_interactive",
        launched_by: Optional[str] = None,
    ) -> Tuple[IssuedToken, str, str]:
        """Validate code + PKCE and issue new token/refresh pair."""
        # Verify and consume code
        row = AuthorizationCode.verify(
            code_plain=code_plain,
            client_id=client_id,
            redirect_uri=redirect_uri,
        )

        if not pkce_verify(code_verifier, row.code_challenge, row.code_challenge_method):
            raise ValueError("invalid_grant: PKCE verification failed")

        AuthorizationCode.consume(row)

        # For MVP we treat the *agent itself* as the resource-owner (no user login)
        agent = Agent.query.filter_by(client_id=client_id).first()
        if not agent:
            raise ValueError("invalid_client")

        # TODO: derive agent_instance_id properly – for now use client_id
        # Delegation not typical for auth code yet but support param
        delegator_sub, final_scope_list = self._process_delegation(
            grant_id=None,  # Not yet supported via /authorize path
            delegate_client_id=client_id,
            requested_scopes=row.scope.split(),
        )

        token_obj, access_token, refresh_token = IssuedToken.create(
            client_id=client_id,
            scope=final_scope_list or row.scope.split(),
            granted_tools=[],
            task_id=str(uuid.uuid4()),
            agent_instance_id=client_id,
            # Required claims placeholders
            agent_type=agent.agent_type,
            agent_model=agent.agent_model,
            agent_provider=agent.agent_provider,
            delegator_sub=delegator_sub,
            launch_reason=launch_reason,
            launched_by=launched_by,
        )
        return token_obj, access_token, refresh_token

    # ------------------------------------------------------------------
    # Introspection / revocation wrappers
    # ------------------------------------------------------------------
    def introspect(self, token: str) -> Optional[IssuedToken]:
        return verify_token(token)

    def revoke(self, token_id: str, revoke_children: bool = False) -> None:
        """Revoke a token and optionally its children.
        
        This delegates to the IssuedToken model methods which handle all audit logging internally.
        """
        # Find the token
        tok = IssuedToken.query.get(token_id)
        if not tok:
            return
            
        # Revoke the token - audit logging handled in tok.revoke()
        tok.revoke(reason="Explicit revocation")
        
        # Revoke children if requested - audit logging handled in tok.revoke_children()
        if revoke_children:
            tok.revoke_children(reason="Parent token revoked")
        
        # Commit changes including audit logs
        db_session.commit()

    # ------------------------------------------------------------------
    # Client Credentials & Refresh grants (moved from router)
    # ------------------------------------------------------------------

    def issue_client_credentials(
        self,
        *,
        client_id: str,
        client_secret: str,
        data: "TokenRequestClientCredentials",
        launched_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Validate an agent and issue tokens (client_credentials)."""
        from werkzeug.security import check_password_hash
        from app.db.models import Agent
        import json, uuid as _uuid
        from app.db.models.audit.task_audit import TaskAuditLog

        # Attempt to get task_id early for logging, generate if not provided
        task_id = data.task_id or str(_uuid.uuid4())
        parent_task_id = None  # Derive task ID from parent token
        parent_token_id = None # Initialize for logging scope

        agent: Agent | None = Agent.query.filter_by(client_id=client_id).first()
        if not agent or not check_password_hash(agent.client_secret_hash, client_secret):
            # Log token denial due to invalid client
            TaskAuditLog.log_event(
                client_id=client_id, token_id="N/A", access_token_hash="N/A",
                task_id=task_id, event_type="token_issue_failed", status="failed",
                details={"reason": "invalid_client"}
            )
            TokenAuditLog.log(
                token_id="N/A", client_id=client_id, event_type="issue_failed",
                task_id=task_id, details={"reason": "invalid_client"}
            )
            raise ValueError("invalid_client")

        scope_list = data.scope.split(" ") if data.scope else []

        # --------------------------------------------------------------
        # Launch reason validation
        # --------------------------------------------------------------
        launch_reason_enum = getattr(data, "launch_reason", LaunchReason.user_interactive)  # type: ignore
        launch_reason = launch_reason_enum.value if isinstance(launch_reason_enum, LaunchReason) else str(launch_reason_enum)

        if launch_reason not in ("user_interactive", "system_job", "agent_delegated"):
            raise ValueError("invalid_launch_reason")

        from app.config import Config
        if launch_reason == "system_job" and client_id not in Config.SYSTEM_CLIENT_IDS:
            raise ValueError("unauthorised_system_client")

        if launch_reason == "agent_delegated":
            if not data.parent_token:
                raise ValueError("parent_token_required_for_agent_delegated")

        # For policy context later
        _launch_ctx = {"launch_reason": launch_reason, "launched_by": launched_by}

        # --------------------------------------------------------------
        # Delegation processing (unified)
        # --------------------------------------------------------------
        try:
            delegator_sub, final_scope_list = self._process_delegation(
                grant_id=getattr(data, "delegation_grant_id", None),
                delegate_client_id=client_id,
                requested_scopes=scope_list or None,
            )
        except ValueError as ve:
            TaskAuditLog.log_event(
                client_id=client_id,
                token_id="N/A",
                access_token_hash="N/A",
                task_id=task_id,
                event_type="token_issue_failed",
                status="failed",
                details={"reason": str(ve)},
            )
            DelegationAuditLog.log_event(
                grant_id=getattr(data, "delegation_grant_id", None),
                action="token_issue_failed",
                delegate_id=client_id,
                details={"reason": str(ve)},
            )
            raise

        if final_scope_list is not None:
            scope_list = list(final_scope_list)

        # Serialize optional complex fields
        delegation_chain_str = (
            json.dumps([step.dict() for step in data.delegation_chain]) if data.delegation_chain else None
        )
        delegation_constraints_str = json.dumps(data.delegation_constraints) if data.delegation_constraints else None
        agent_capabilities_str = json.dumps(data.agent_capabilities) if data.agent_capabilities else None
        agent_attestation_str = data.agent_attestation.json() if data.agent_attestation else None

        if data.parent_token:
            p_tok = verify_token(data.parent_token)
            if not p_tok:
                # Log token denial due to invalid parent token
                TaskAuditLog.log_event(
                    client_id=client_id, token_id="N/A", access_token_hash="N/A",
                    task_id=task_id, event_type="token_issue_failed", status="failed",
                    details={"reason": "invalid_parent_token"}
                )
                TokenAuditLog.log(
                    token_id="N/A", client_id=client_id, event_type="issue_failed",
                    task_id=task_id, parent_task_id="unknown", # Can't get parent task ID from invalid token
                    details={"reason": "invalid_parent_token"}
                )
                raise ValueError("invalid parent_token")
            parent_token_id = p_tok.token_id
            parent_task_id = p_tok.task_id

        # ------------------------------------------------------------------
        # Policy evaluation with priority / deny overrides
        # ------------------------------------------------------------------
        from app.core.registry import get_policy_engine
        policy_engine = get_policy_engine()

        policy_ctx = {
            "client_id": client_id,
            "scopes": scope_list,
            "granted_tools": data.required_tools or [],
            "response_type": "client_credentials",
            "agent": {
                "is_active": agent.is_active,
                "is_external": False,  # Assuming internal by default for client_credentials
                "status": "active" if agent.is_active else "inactive", # Derive status
                "agent_type": agent.agent_type,
                "agent_model": agent.agent_model,
                "agent_version": agent.agent_version,
                "agent_provider": agent.agent_provider
            },
            **_launch_ctx,
        }

        policy_decision = policy_engine.evaluate(policy_ctx)
        if not policy_decision.get("allowed", False):
            # Log policy denial event before raising error
            denying_policy_id = policy_decision.get('denied_by')
            PolicyAuditLog.log(
                client_id=client_id,
                action="token_issue_attempt",
                decision="denied",
                reason=f"denied_by_policy {denying_policy_id}",
                policy_id=denying_policy_id,
                resource_type="token",
                task_id=task_id,
                parent_task_id=parent_task_id,
                context=policy_ctx
            )
            # raise with details; routers will convert to HTTPException
            raise ValueError(f"access_denied: denied_by_policy {denying_policy_id}")

        # Create IssuedToken
        # Create IssuedToken - Token.create handles all audit logging in the correct sequence
        token_obj, access_token, refresh_token = IssuedToken.create(
            client_id=client_id,
            scope=scope_list,
            granted_tools=data.required_tools,
            task_id=task_id,
            agent_instance_id=data.agent_instance_id,
            agent_type=data.agent_type,
            agent_model=data.agent_model,
            agent_provider=data.agent_provider,
            delegator_sub=delegator_sub or data.delegator_sub,
            agent_version=agent.agent_version,
            delegation_chain=delegation_chain_str,
            delegation_purpose=data.delegation_purpose,
            delegation_constraints=delegation_constraints_str,
            agent_capabilities=agent_capabilities_str,
            agent_trust_level=data.agent_trust_level,
            agent_attestation=agent_attestation_str,
            agent_context_id=data.agent_context_id,
            task_description=data.task_description,
            parent_task_id=parent_task_id,
            parent_token_id=parent_token_id,
            scope_inheritance_type=data.scope_inheritance_type,
            code_challenge=data.code_challenge,
            code_challenge_method=data.code_challenge_method,
            launch_reason=launch_reason,
            launched_by=launched_by,
        )

        # Commit the session to persist token and all audit logs
        db_session.commit()

        expires_in = int((token_obj.expires_at - token_obj.issued_at).total_seconds())
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": expires_in,
            "scope": scope_list,
            "task_id": token_obj.task_id,
            "token_id": token_obj.token_id,
            "delegator_sub": delegator_sub or data.delegator_sub,
            "launch_reason": launch_reason,
            "launched_by": launched_by,
        }

    def refresh_token(
        self,
        *,
        refresh_token_raw: str,
        scope: Optional[str] = None,
        launch_reason: str = "user_interactive",
        launched_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Rotate refresh token and return new pair."""
        from app.db.models.audit.task_audit import TaskAuditLog
        from app.db.models.audit.policy_audit import PolicyAuditLog
        from app.db.models.audit.scope_audit import ScopeAuditLog
        from datetime import datetime as _dt

        # 1. Find the *old* token by the provided raw refresh token string.
        # Note: We are comparing against the raw token stored in refresh_token_hash for simplicity.
        # In production, this should use a proper hash comparison.
        old_token = IssuedToken.query.filter_by(refresh_token_hash=refresh_token_raw).first()

        if not old_token:
            TaskAuditLog.log_event(
                client_id="unknown", token_id="N/A", access_token_hash="N/A", task_id="unknown",
                event_type="token_refresh_failed", status="failed", details={"reason": "invalid_grant: Refresh token not found"}
            )
            TokenAuditLog.log(
                token_id="N/A", client_id="unknown", event_type="refresh_failed", task_id="unknown",
                details={"reason": "invalid_grant: Refresh token not found"}
            )
            raise ValueError("invalid_grant: Refresh token not found")
        if old_token.is_revoked:
            TaskAuditLog.log_event(
                client_id=old_token.client_id, token_id=old_token.token_id, access_token_hash="N/A", task_id=old_token.task_id,
                event_type="token_refresh_failed", status="failed", details={"reason": "invalid_grant: Refresh token revoked"}
            )
            TokenAuditLog.log(
                token_id=old_token.token_id, client_id=old_token.client_id, event_type="refresh_failed", task_id=old_token.task_id,
                details={"reason": "invalid_grant: Refresh token revoked"}
            )
            raise ValueError("invalid_grant: Refresh token revoked")
        if old_token.expires_at < _dt.utcnow(): # Also check expiry
            TaskAuditLog.log_event(
                client_id=old_token.client_id, token_id=old_token.token_id, access_token_hash="N/A", task_id=old_token.task_id,
                event_type="token_refresh_failed", status="failed", details={"reason": "invalid_grant: Refresh token expired"}
            )
            TokenAuditLog.log(
                token_id=old_token.token_id, client_id=old_token.client_id, event_type="refresh_failed", task_id=old_token.task_id,
                details={"reason": "invalid_grant: Refresh token expired"}
            )
            raise ValueError("invalid_grant: Refresh token expired")

        # 2. Call the token's refresh method to handle revocation, creation, and internal audit logging
        try:
            new_token_obj, new_access_token, new_refresh_token = old_token.refresh(
                requested_scope_str=scope,
                launch_reason=launch_reason or old_token.launch_reason,
                launched_by=launched_by or old_token.launched_by,
            )
        except ValueError as ve: # Catch scope validation errors from refresh()
            # Log token denial due to invalid scope during refresh
            TaskAuditLog.log_event(
                client_id=old_token.client_id, token_id=old_token.token_id, access_token_hash="N/A", task_id=old_token.task_id,
                event_type="token_refresh_failed", status="failed", details={"reason": f"invalid_scope: {ve}", "requested_scope": scope}
            )
            TokenAuditLog.log(
                token_id=old_token.token_id, client_id=old_token.client_id, event_type="refresh_failed", task_id=old_token.task_id,
                details={"reason": f"invalid_scope: {ve}", "requested_scope": scope}
            )
            raise ValueError(f"invalid_scope: {ve}")

        # 3. Commit the transaction (includes revocation of old, creation of new)
        # The IssuedToken.refresh() method adds objects to the session.
        db_session.commit()

        # 4. Log other audit events (Task, Policy, Scope) related to the *new* token
        # We get the necessary details from the new_token_obj returned by refresh()
        new_scope_list = new_token_obj.scopes.split()
        new_granted_tools = new_token_obj.granted_tools.split()

        TaskAuditLog.log_event(
            client_id=new_token_obj.client_id,
            token_id=new_token_obj.token_id,
            access_token_hash=new_token_obj.access_token_hash,
            task_id=new_token_obj.task_id,
            parent_task_id=new_token_obj.parent_task_id,
            event_type="token_refreshed", # Specific event type
            status="success",
            details={"scopes": new_scope_list, "granted_tools": new_granted_tools, "old_token_id": old_token.token_id}
        )
        PolicyAuditLog.log(
            client_id=new_token_obj.client_id,
            action="token_refreshed",
            decision="success",
            resource_type="token",
            resource_id=new_token_obj.token_id,
            task_id=new_token_obj.task_id,
            parent_task_id=new_token_obj.parent_task_id,
            context={"scopes": new_scope_list, "granted_tools": new_granted_tools, "old_token_id": old_token.token_id}
        )
        for scope_name in new_scope_list:
            ScopeAuditLog.log(
                scope_id=scope_name,
                client_id=new_token_obj.client_id,
                action="granted", # Still granted for the new token
                task_id=new_token_obj.task_id,
                parent_task_id=new_token_obj.parent_task_id,
                details={"token_id": new_token_obj.token_id, "refresh": True}
            )

        # 5. Prepare and return the response dictionary
        expires_in = int((new_token_obj.expires_at - new_token_obj.issued_at).total_seconds())
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "Bearer",
            "expires_in": expires_in,
            "scope": new_scope_list,
            "task_id": new_token_obj.task_id,
            "token_id": new_token_obj.token_id,
            "launch_reason": new_token_obj.launch_reason,
            "launched_by": new_token_obj.launched_by,
        }

    # ------------------------------------------------------------------
    # Authorization endpoint with policy-driven consent flow
    # ------------------------------------------------------------------
    def authorize_request(
        self,
        response_type: str,
        client_id: str,
        redirect_uri: str,
        scope: Optional[str] = None,
        state: Optional[str] = None,
        code_challenge: Optional[str] = None,
        code_challenge_method: str = "S256",
    ) -> Dict[str, Any]:
        """
        Handle the authorization (PKCE) request with optional human-in-the-loop consent.
        Returns a dict indicating either a consent prompt or an auto-approved redirect response.
        """
        from urllib.parse import urlencode, urlparse, urlunparse
        from app.core.registry import get_policy_engine
        from app.db.models import Agent

        # 1. Parameter validation
        if response_type != "code":
            raise ValueError("unsupported_response_type")
        if not code_challenge:
            raise ValueError("code_challenge required")
        if code_challenge_method.upper() not in ("PLAIN", "S256"):
            raise ValueError("invalid code_challenge_method")

        # 2. Client validation
        agent = Agent.query.filter_by(client_id=client_id).first()
        if not agent or not agent.is_active:
            raise ValueError("invalid_client")
        if not redirect_uri:
            raise ValueError("redirect_uri required")

        # Prepare scopes list
        scopes_list = scope.split() if scope else []

        # 3. Policy-driven consent check
        policy_engine = get_policy_engine()
        if policy_engine.requires_human_approval(client_id, scopes_list, response_type):
            # Prompt the client/UI for consent
            return {
                "consent_required": True,
                "client_id": client_id,
                "scopes": scopes_list,
                "state": state,
                "redirect_uri": redirect_uri,
            }

        # 4. Auto-approval: generate authorization code
        plaintext_code, returned_state = self.create_authorization_code(
            client_id=client_id,
            redirect_uri=redirect_uri,
            scope=scopes_list,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            state=state,
        )

        # 5. Build redirect URL with code and state
        parsed = urlparse(redirect_uri)
        existing = parsed.query
        query_params = {"code": plaintext_code}
        if state:
            query_params["state"] = state
        new_query = (existing + "&" if existing else "") + urlencode(query_params)
        redirect_url = urlunparse(parsed._replace(query=new_query))

        return {
            "consent_required": False,
            "redirect_url": redirect_url,
            "code": plaintext_code,
            "state": state,
            "scope": scopes_list,
            "client_id": client_id,
        }

    # ------------------------------------------------------------------
    # Internal helper for delegation handling (unified flow)
    # ------------------------------------------------------------------
    def _process_delegation(
        self,
        *,
        grant_id: Optional[str],
        delegate_client_id: str,
        requested_scopes: Optional[List[str]],
    ) -> Tuple[Optional[str], Optional[List[str]]]:
        """Validate DelegationGrant and return (delegator_sub, final_scope).

        If ``grant_id`` is None → returns (None, requested_scopes).
        Raises ValueError on invalid grant.
        """
        if not grant_id:
            # No delegation grant provided – treat as self-issued token.
            return None, requested_scopes  # self-issued

        # Perform a **lazy import** here to avoid circular dependencies
        # between `app.core.oauth.engine` and `app.core.registry` which
        # itself imports the OAuth getter.
        from app.core.registry import get_delegation_engine  # local import

        delegation_engine = get_delegation_engine()
        grant = delegation_engine.validate_grant(
            grant_id=grant_id,
            delegate_id=delegate_client_id,
            requested_scopes=requested_scopes,
        )

        # Final scope is requested or full grant scope
        final_scope = requested_scopes if requested_scopes is not None else grant.scope

        # Emit audit handled in validate_grant on success.
        return cast(str, grant.principal_id), final_scope 