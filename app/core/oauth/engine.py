"""Centralised OAuth business logic used by routers and services."""
from __future__ import annotations

import uuid
import traceback
from typing import List, Dict, Any, Optional, Tuple, cast
from datetime import timedelta

# Database models
from app.db.models import Agent, IssuedToken
from app.db.models.audit.token_audit import TokenAuditLog
from app.db.models.audit.delegation_audit import DelegationAuditLog
from app.core.oauth.code_handler import code_handler
from app.core.oauth.token_handler import token_handler

# Utilities
from app.core.oauth.utils import verify_token
from app.schemas.oauth import TokenRequestClientCredentials, LaunchReason
from app.utils.logger import logger

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
        """Generate plaintext code & persist row. Returns (code, state).

        This is now just a thin wrapper around `oauth.code_handler.create_authorization_code`
        to keep this facade lean while preserving backwards-compatible import
        paths throughout the rest of the application.
        """
        # Local import to avoid heavy module load if this method isn't used.
        return code_handler.create_authorization_code(
            client_id=client_id,
            redirect_uri=redirect_uri,
            scope=scope,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            state=state,
            lifetime_seconds=lifetime_seconds,
        )

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
        # OPA authorization for auth-code exchange
        from app.core.policy.opa_client import opa_client
        input_data = {
            "client_id": client_id,
            "code": code_plain,
            "redirect_uri": redirect_uri,
            # NOTE: Requested scopes are not available at this stage; they will be
            # validated later in `token_handler.exchange_code_for_token`. If the
            # policy needs scopes, it can introspect the code or be checked after
            # issuance.
            "launch_reason": launch_reason,
            "launched_by": launched_by,
        }
        allowed = opa_client.query_bool_sync("allow_auth_code", input_data)
        if not allowed:
            raise ValueError("access_denied: denied_by_policy")
        return token_handler.exchange_code_for_token(
            client_id=client_id,
            code_plain=code_plain,
            redirect_uri=redirect_uri,
            code_verifier=code_verifier,
            access_expires_in=access_expires_in,
            launch_reason=launch_reason,
            launched_by=launched_by,
        )

    # ------------------------------------------------------------------
    # Introspection / revocation wrappers
    # ------------------------------------------------------------------
    def introspect(self, token: str) -> Optional[IssuedToken]:
        """Introspect a token to validate and return its details."""
        return token_handler.introspect(token)

    def revoke(self, token_id: str, revoke_children: bool = False) -> None:
        """Revoke a token and optionally its children."""
        token_handler.revoke(token_id=token_id, revoke_children=revoke_children)

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
        return token_handler.issue_client_credentials(
            client_id=client_id,
            client_secret=client_secret,
            data=data,
            launched_by=launched_by,
        )

    def refresh_token(
        self,
        *,
        refresh_token_raw: str,
        scope: Optional[str] = None,
        launch_reason: str = "user_interactive",
        launched_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Rotate refresh token and return new pair."""
        # OPA authorization for refresh grant
        from app.core.policy.opa_client import opa_client
        input_data = {
            "refresh_token": refresh_token_raw,
            "requested_scope": scope,
            "launch_reason": launch_reason,
            "launched_by": launched_by,
        }
        allowed = opa_client.query_bool_sync("allow_refresh", input_data)
        if not allowed:
            raise ValueError("access_denied: denied_by_policy")
        return token_handler.refresh_token(
            refresh_token_raw=refresh_token_raw,
            scope=scope,
            launch_reason=launch_reason,
            launched_by=launched_by,
        )

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

        # OPA policy-driven consent check
        from app.core.policy.opa_client import opa_client
        consent_input = {
            "client_id": client_id,
            "scopes": scopes_list,
            "response_type": response_type,
        }
        consent_required = opa_client.query_bool_sync("requires_human_approval", consent_input)
        if consent_required:
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

        # OPA delegation policy check
        from app.core.policy.opa_client import opa_client
        deleg_input = {
            "grant_id": grant_id,
            "delegate_id": delegate_client_id,
            "requested_scopes": requested_scopes,
        }
        allowed = opa_client.query_bool_sync("allow_delegation", deleg_input)
        if not allowed:
            raise ValueError("delegation_denied_by_policy")

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