"""Token handling utilities extracted from OAuthEngine.

This module centralises all token life-cycle operations:
- exchange_code_for_token
- issue_client_credentials
- refresh_token
- introspect
- revoke

Used by `OAuthEngine` to keep the facade lean while logic lives here.
"""
from __future__ import annotations

import uuid
import json
import traceback
from datetime import datetime as _dt, timedelta
from typing import Any, Dict, Optional, Tuple, List, cast

from werkzeug.security import check_password_hash

from agentictrust.db.models import Agent, IssuedToken
from agentictrust.db.models.audit.task_audit import TaskAuditLog
from agentictrust.db.models.audit.token_audit import TokenAuditLog
from agentictrust.db.models.audit.policy_audit import PolicyAuditLog
from agentictrust.db.models.audit.scope_audit import ScopeAuditLog
from agentictrust.db.models.audit.delegation_audit import DelegationAuditLog
from agentictrust.core.oauth.code_handler import code_handler
from agentictrust.core.oauth.utils import verify_token
from agentictrust.config import Config
from agentictrust.schemas.oauth import TokenRequestClientCredentials, LaunchReason
from agentictrust.utils.logger import logger

class TokenHandler:
    """Handles token issuance, refresh, introspection, and revocation."""
    def __init__(self):
        pass

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
        try:
            logger.info("Exchanging authorization code for token (client: %s)", client_id)

            # 1. Verify and consume code (incl. PKCE)
            row = code_handler.verify_and_consume(
                code_plain=code_plain,
                client_id=client_id,
                redirect_uri=redirect_uri,
                code_verifier=code_verifier,
            )

            # 2. Verify client exists
            agent = Agent.query.filter_by(client_id=client_id).first()
            if not agent:
                logger.warning("Invalid client during token exchange: %s", client_id)
                raise ValueError("invalid_client")

            # 3. Delegation (placeholder for auth-code path)
            delegator_sub: Optional[str] = None
            final_scope_list: List[str] = row.scope.split()

            # 4. Issue token
            task_id = str(uuid.uuid4())
            try:
                token_obj, access_token, refresh_token = IssuedToken.create(
                    client_id=client_id,
                    scope=final_scope_list,
                    granted_tools=[],
                    task_id=task_id,
                    agent_instance_id=client_id,
                    agent_type=agent.agent_type,
                    agent_model=agent.agent_model,
                    agent_provider=agent.agent_provider,
                    delegator_sub=delegator_sub,
                    launch_reason=launch_reason,
                    launched_by=launched_by,
                    expires_in=access_expires_in,
                )
                logger.info(
                    "Successfully issued token for client %s (token ID: %s)",
                    client_id,
                    token_obj.token_id,
                )
                return token_obj, access_token, refresh_token
            except Exception as token_error:
                logger.error(
                    "Error creating token for client %s: %s", client_id, token_error
                )
                raise ValueError(f"Failed to create token: {token_error}") from token_error
        except ValueError:
            raise
        except Exception as e:
            logger.error(
                "Unexpected error during token exchange for client %s: %s", client_id, e
            )
            logger.debug("Exception details: %s", traceback.format_exc())
            raise RuntimeError(f"Failed to exchange code for token: {e}") from e

    def issue_client_credentials(
        self,
        *,
        client_id: str,
        client_secret: str,
        data: TokenRequestClientCredentials,
        launched_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Validate an agent and issue tokens (client_credentials)."""
        # 1. Authenticate client
        task_id = data.task_id or str(uuid.uuid4())
        parent_task_id: Optional[str] = None
        parent_token_id: Optional[str] = None

        agent = Agent.query.filter_by(client_id=client_id).first()
        if not agent or not check_password_hash(
            agent.client_secret_hash, client_secret
        ):
            TaskAuditLog.log_event(
                client_id=client_id,
                token_id="N/A",
                access_token_hash="N/A",
                task_id=task_id,
                event_type="token_issue_failed",
                status="failed",
                details={"reason": "invalid_client"},
            )
            TokenAuditLog.log(
                token_id="N/A",
                client_id=client_id,
                event_type="issue_failed",
                task_id=task_id,
                details={"reason": "invalid_client"},
                delegator_sub=None,
                delegation_chain=None,
            )
            raise ValueError("invalid_client")

        # 2. Scopes
        scope_list = data.scope.split(" ") if data.scope else []

        # ----- Policy check (Task4) ----------------------------
        from agentictrust.core.registry import get_policy_engine
        policy_engine = get_policy_engine()
        allowed = policy_engine.is_allowed(
            client_id=client_id,
            action="token_issue_client_credentials",
            input_ctx={
                "client_id": client_id,
                "requested_scopes": scope_list,
                "launch_reason": getattr(data, "launch_reason", None),
            },
        )
        if not allowed:
            raise ValueError("access_denied_by_policy")

        # 3. Launch reason
        launch_reason_enum = getattr(
            data, "launch_reason", LaunchReason.user_interactive
        )
        launch_reason = (
            launch_reason_enum.value
            if isinstance(launch_reason_enum, LaunchReason)
            else str(launch_reason_enum)
        )
        if launch_reason not in (
            "user_interactive",
            "system_job",
            "agent_delegated",
        ):
            raise ValueError("invalid_launch_reason")

        if launch_reason == "system_job" and client_id not in Config.SYSTEM_CLIENT_IDS:
            raise ValueError("unauthorised_system_client")

        if launch_reason == "agent_delegated" and not data.parent_token:
            raise ValueError("parent_token_required_for_agent_delegated")

        # 4. Delegation
        from agentictrust.core.registry import get_delegation_engine
        try:
            grant_id = getattr(data, "delegation_grant_id", None)
            if not grant_id:
                delegator_sub: Optional[str] = None
                final_scope_list = scope_list
            else:
                engine = get_delegation_engine()
                grant = engine.validate_grant(
                    grant_id=grant_id,
                    delegate_id=client_id,
                    requested_scopes=scope_list or None,
                )
                delegator_sub = cast(str, grant.principal_id)
                final_scope_list = (
                    scope_list if scope_list else grant.scope
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

        # 5. Parent token
        if data.parent_token:
            parent = verify_token(data.parent_token)
            if not parent:
                TaskAuditLog.log_event(
                    client_id=client_id,
                    token_id="N/A",
                    access_token_hash="N/A",
                    task_id=task_id,
                    event_type="token_issue_failed",
                    status="failed",
                    details={"reason": "invalid_parent_token"},
                )
                TokenAuditLog.log(
                    token_id="N/A",
                    client_id=client_id,
                    event_type="issue_failed",
                    task_id=task_id,
                    parent_task_id="unknown",
                    details={"reason": "invalid_parent_token"},
                    delegator_sub=None,
                    delegation_chain=None,
                )
                raise ValueError("invalid_parent_token")
            parent_token_id = parent.token_id
            parent_task_id = parent.task_id
            # Capture parent token details for policy evaluation
            parent_details = {
                "token_id": parent.token_id,
                "task_id": parent.task_id,
                "client_id": parent.client_id,
                "scopes": parent.scopes.split(),
            }
        else:
            parent_details = None

        # 6. Policy evaluation via OPA
        policy_ctx = {
            "client_id": client_id,
            "scopes": scope_list,
            "granted_tools": data.required_tools or [],
            "response_type": "client_credentials",
            "agent": {
                "is_active": agent.is_active,
                "status": "active" if agent.is_active else "inactive",
                "agent_type": agent.agent_type,
                "agent_model": agent.agent_model,
                "agent_version": agent.agent_version,
                "agent_provider": agent.agent_provider,
            },
            "launch_reason": launch_reason,
            "launched_by": launched_by,
            "parent": parent_details,
        }
        from agentictrust.core.policy.opa_client import opa_client
        policy_ctx["response_type"] = "client_credentials"
        input_data = {
            "refresh_token": data.parent_token,
            "client_id": client_id,
            "scopes": scope_list,
            "granted_tools": data.required_tools or [],
            "response_type": "client_credentials",
            "agent": {
                "is_active": agent.is_active,
                "status": "active" if agent.is_active else "inactive",
                "agent_type": agent.agent_type,
                "agent_model": agent.agent_model,
                "agent_version": agent.agent_version,
                "agent_provider": agent.agent_provider,
            },
            "launch_reason": launch_reason,
            "launched_by": launched_by,
            "parent": parent_details,
        }
        allowed = opa_client.query_bool_sync("allow_token_issue", input_data)
        if not allowed:
            PolicyAuditLog.log(
                client_id=client_id,
                action="token_issue_attempt",
                decision="denied",
                reason="denied_by_opa",
                resource_type="token",
                task_id=task_id,
                parent_task_id=parent_task_id,
                details=policy_ctx,
            )
            raise ValueError("access_denied: denied_by_policy")

        # 7. Issue token
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
            delegation_chain=(
                json.dumps([step.dict() for step in data.delegation_chain])
                if data.delegation_chain
                else None
            ),
            delegation_purpose=data.delegation_purpose,
            delegation_constraints=(
                json.dumps(data.delegation_constraints)
                if data.delegation_constraints
                else None
            ),
            agent_capabilities=(
                json.dumps(data.agent_capabilities)
                if data.agent_capabilities
                else None
            ),
            agent_trust_level=data.agent_trust_level,
            agent_attestation=(
                data.agent_attestation.json()
                if data.agent_attestation
                else None
            ),
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
        from datetime import datetime
        try:
            old_token = IssuedToken.query.filter_by(
                refresh_token_hash=refresh_token_raw
            ).first()
            if not old_token:
                raise ValueError("invalid_grant: Refresh token not found")
            if old_token.is_revoked:
                raise ValueError("invalid_grant: Refresh token revoked")
            if old_token.expires_at < _dt.utcnow():
                raise ValueError("invalid_grant: Refresh token expired")

            try:
                new_obj, new_access, new_refresh = old_token.refresh(
                    requested_scope_str=scope,
                    launch_reason=launch_reason or old_token.launch_reason,
                    launched_by=launched_by or old_token.launched_by,
                )
            except ValueError as ve:
                raise

            new_scope = new_obj.scopes.split()
            new_tools = new_obj.granted_tools.split()
            for scope_name in new_scope:
                ScopeAuditLog.log(
                    scope_id=scope_name,
                    client_id=new_obj.client_id,
                    action="granted",
                    task_id=new_obj.token_id,
                    parent_task_id=new_obj.parent_token_id,
                    details={"token_id": new_obj.token_id, "refresh": True},
                )
            return {
                "access_token": new_access,
                "refresh_token": new_refresh,
                "token_type": "Bearer",
                "expires_in": int((new_obj.expires_at - new_obj.issued_at).total_seconds()),
                "scope": new_scope,
                "task_id": new_obj.task_id,
                "token_id": new_obj.token_id,
                "launch_reason": new_obj.launch_reason,
                "launched_by": new_obj.launched_by,
            }
        except ValueError as ve:
            logger.error("Refresh flow error: %s", ve)
            raise
        except Exception as e:
            logger.error("Unexpected error in refresh_token: %s", e)
            logger.debug("Traceback: %s", traceback.format_exc())
            raise RuntimeError(f"Failed to refresh token: {e}") from e

    def introspect(self, token: str) -> Optional[IssuedToken]:
        """Introspect a token to validate and return its details."""
        try:
            obj = verify_token(token)
            if obj:
                logger.debug("Token introspection successful (ID: %s)", obj.token_id)
            else:
                logger.debug("Token introspection failed: invalid or not found")
            return obj
        except Exception as e:
            logger.error("Error during token introspection: %s", e)
            logger.debug("Traceback: %s", traceback.format_exc())
            return None

    def revoke(self, token_id: str, revoke_children: bool = False) -> None:
        """Revoke a token and optionally its children."""
        try:
            tok = IssuedToken.query.get(token_id)
            if not tok:
                logger.warning(
                    "Attempted to revoke non-existent token %s", token_id
                )
                return
            tok.revoke(reason="Explicit revocation")
            if revoke_children:
                tok.revoke_children(reason="Parent token revoked")
        except Exception as e:
            logger.error("Error revoking token %s: %s", token_id, e)
            logger.debug("Traceback: %s", traceback.format_exc())

# Single shared instance
token_handler = TokenHandler()
