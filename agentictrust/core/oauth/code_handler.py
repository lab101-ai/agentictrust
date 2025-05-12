"""Authorization code handling utilities extracted from OAuthEngine.

This module provides a single-responsibility function for creating PKCE
authorization codes. It is imported by `OAuthEngine.create_authorization_code`
so that the engine itself remains a thin facade while the heavy‐lifting logic
lives in a dedicated, testable module.
"""
from __future__ import annotations

import secrets
import traceback
from typing import List, Optional, Tuple, Union

from agentictrust.db.models.authorization_code import AuthorizationCode
from agentictrust.utils.logger import logger
from agentictrust.core.oauth.utils import pkce_verify

# Type alias for the ``scope`` parameter (string or list of strings)
ScopeType = Union[str, List[str], None]


class CodeHandler:
    """Authorization code handling utilities extracted from OAuthEngine."""

    def __init__(self):
        pass

    def create_authorization_code(
        self,
        *,
        client_id: str,
        redirect_uri: str,
        scope: ScopeType = None,
        code_challenge: str,
        code_challenge_method: str = "S256",
        state: Optional[str] = None,
        lifetime_seconds: int = 600,
    ) -> Tuple[str, str]:
        """Generate a plaintext authorization code and persist it.

        Parameters
        ----------
        client_id: str
            OAuth client identifier (Agent ID).
        redirect_uri: str
            Redirect URI that must match the one provided during the token
            exchange.
        scope: str | list[str] | None, default ``None``
            Requested scopes. If a list is supplied it will be normalised to a
            space-delimited string before storage.
        code_challenge: str
            PKCE code challenge.
        code_challenge_method: str, default ``"S256"``
            Transformation method for the challenge (``"S256"`` or ``"plain"``).
        state: str | None, default ``None``
            Optional opaque value supplied by the client that will be returned as
            long as the flow completes successfully.
        lifetime_seconds: int, default ``600`` (10 minutes)
            How long the authorisation code should remain valid.

        Returns
        -------
        tuple[str, str]
            The plaintext authorisation code *and* the (unchanged) state value so
            that callers can forward it back to the user.
        """
        try:
            # 1. Generate a cryptographically-secure random code.
            plaintext_code: str = secrets.token_urlsafe(32)

            # 2. Serialize the requested scope into a string if needed.
            normalised_scope: str | None
            if isinstance(scope, list):
                normalised_scope = " ".join(scope)
            else:
                normalised_scope = scope

            logger.info("Creating authorisation code for client %s", client_id)
            logger.debug(
                "Code-challenge method: %s | Lifetime: %ss",
                code_challenge_method,
                lifetime_seconds,
            )

            # 3. Persist the new authorisation code.
            AuthorizationCode.create(
                code_plain=plaintext_code,
                client_id=client_id,
                scope=normalised_scope or "",
                redirect_uri=redirect_uri,
                code_challenge=code_challenge,
                code_challenge_method=code_challenge_method,
                lifetime_seconds=lifetime_seconds,
            )

            logger.info("Successfully created authorisation code for client %s", client_id)
            return plaintext_code, state  # type: ignore[return-value]

        except Exception as exc:  # pragma: no cover – catch-all for unexpected errors
            logger.error("Error creating authorisation code for client %s: %s", client_id, exc)
            logger.debug("Traceback: %s", traceback.format_exc())
            # Bubble up as runtime error so that the caller can translate it into
            # an OAuth-compatible error response (e.g. HTTP 500).
            raise RuntimeError(f"Failed to create authorisation code: {exc}") from exc

    def verify_and_consume(
        self,
        *,
        code_plain: str,
        client_id: str,
        redirect_uri: str,
        code_verifier: str,
    ) -> AuthorizationCode:
        """Verify PKCE code, consume authorization code, and return the row."""
        try:
            row = AuthorizationCode.verify(
                code_plain=code_plain,
                client_id=client_id,
                redirect_uri=redirect_uri,
            )
        except ValueError as code_error:
            logger.warning("Authorization code verification failed: %s", code_error)
            raise ValueError(f"invalid_grant: {code_error}") from code_error

        # PKCE check
        if not pkce_verify(code_verifier, row.code_challenge, row.code_challenge_method):
            logger.warning("PKCE verification failed for client %s", client_id)
            raise ValueError("invalid_grant: PKCE verification failed")

        # Consume the code so it can't be replayed
        AuthorizationCode.consume(row)
        logger.debug("Authorization code consumed successfully")
        return row


code_handler = CodeHandler()
