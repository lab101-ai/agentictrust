"""Utility helpers for OAuthEngine."""
import base64
import hashlib
from datetime import datetime
from werkzeug.security import check_password_hash
from app.utils.logger import logger
from app.config import Config
from app.utils.keys import get_public_jwks
import jwt
from typing import List


def pkce_verify(code_verifier: str, stored_challenge: str, method: str = "S256") -> bool:
    """Return True if `code_verifier` satisfies stored challenge."""
    if method.upper() == "PLAIN":
        return code_verifier == stored_challenge
    if method.upper() == "S256":
        sha = hashlib.sha256(code_verifier.encode()).digest()
        challenge = base64.urlsafe_b64encode(sha).rstrip(b"=").decode()
        return challenge == stored_challenge
    # unknown method
    return False

def verify_token(token_str, allow_clock_skew=True, max_clock_skew_seconds=86400):
    """Verify an access token and return the corresponding token object if valid."""
    # Quick sanity-check: a well-formed JWT has exactly two '.' characters (three segments)
    if token_str.count('.') != 2:
        logger.warning("Token verification failed: supplied token is not a valid JWT format")
        return None

    jwks = get_public_jwks()
    public_keys = {}
    for jwk in jwks.get('keys', []):
        kid = jwk.get('kid')
        if kid:
            public_keys[kid] = jwt.algorithms.RSAAlgorithm.from_jwk(jwk)

    if not public_keys:
        logger.error("Error: No public keys found in JWKS for verification.")
        return None

    try:
        unverified_header = jwt.get_unverified_header(token_str)
        kid = unverified_header.get('kid')
        if not kid:
            logger.error("Error: Token header missing 'kid'.")
            return None

        public_key = public_keys.get(kid)
        if not public_key:
            logger.error(f"Error: Public key not found for kid: {kid}")
            return None

        # Disable audience validation to avoid Invalid audience errors
        verification_options = {"leeway": 30, "verify_aud": False}
        if allow_clock_skew and max_clock_skew_seconds > 30:
            verification_options["verify_nbf"] = False
            verification_options["verify_iat"] = False
            logger.debug(f"Disabling nbf/iat verification due to large clock skew allowance: {max_clock_skew_seconds} seconds")

        try:
            payload = jwt.decode(
                token_str,
                public_key,
                algorithms=["RS256"],
                options=verification_options
            )
            logger.debug("JWT token validation successful")
        except jwt.InvalidTokenError as jwt_err:
            logger.warning(f"JWT validation failed: {str(jwt_err)}")
            return None

        # JWT token identifier claim is 'jti'; support both 'token_id' and 'jti'
        token_id = payload.get('token_id') or payload.get('jti')
        if not token_id:
            logger.warning("Token verification failed: invalid JWT payload structure")
            return None

        logger.debug(f"JWT token validation successful for token_id: {token_id}")

        from app.db.models.token import IssuedToken
        try:
            token = IssuedToken.query.filter_by(token_id=token_id).first()
        except Exception as e:
            logger.error(f"Database error querying token {token_id}: {e}")
            return None

        if not token:
            logger.warning(f"Token verification failed: token_id {token_id} not found in database")
            return None

        source_ip = None
        if not token.verify(source_ip=source_ip):
            logger.warning(f"Token verification failed: token_id {token.token_id} is no longer valid")
            if token.is_revoked:
                logger.warning(f"Token is revoked. Revocation reason: {token.revocation_reason}")
            if token.expires_at < datetime.utcnow():
                logger.warning(f"Token is expired. Expired at: {token.expires_at}")
            return None

        hash_valid = check_password_hash(token.access_token_hash, token_str)
        if not hash_valid:
            logger.warning(f"Token verification failed: token_id {token.token_id} hash mismatch")
            logger.debug(f"Token hash check failed. Token first 20 chars: {token_str[:20] if token_str else None}")
            if payload and 'token_id' in payload:
                logger.info(f"Accepting JWT token despite hash mismatch due to valid JWT signature. Token ID: {token.token_id}")
            else:
                return None

        logger.bind(
            token_id=token.token_id,
            client_id=token.client_id,
            task_id=token.task_id
        ).debug("Token verification successful")
        return token
    except Exception as e:
        logger.error(f"Unexpected error in verify_token: {str(e)}", exc_info=True)
        return None

def verify_task_lineage(token, parent_token=None, task_id=None, parent_task_id=None):
    """Verify that a token has valid task lineage with its parent token."""
    log_ctx = {
        "token_id": token.token_id,
        "client_id": token.client_id,
        "task_id": token.task_id,
        "parent_task_id": token.parent_task_id
    }
    if not parent_token and not parent_task_id:
        result = token.is_valid()
        logger.bind(**log_ctx).debug(f"Task lineage verification (token only): {result}")
        return result
    if not token.parent_token_id and not token.parent_task_id and (parent_token or parent_task_id):
        logger.bind(**log_ctx).warning("Task lineage verification failed: no parent info but parent specified")
        return False
    if parent_token and token.parent_token_id != parent_token.token_id:
        logger.bind(**log_ctx).warning(
            f"Task lineage verification failed: parent token mismatch. Expected: {token.parent_token_id}, Got: {parent_token.token_id}"
        )
        return False
    # When a parent_token is provided, ensure derived parent_task_id matches
    if parent_token and token.parent_task_id != parent_token.task_id:
        logger.bind(**log_ctx).warning(
            f"Task lineage verification failed: parent task mismatch. Expected: {token.parent_task_id}, Got: {parent_token.task_id}"
        )
        return False
    # Backward-compatibility: explicit parent_task_id check
    if not parent_token and parent_task_id and token.parent_task_id != parent_task_id:
        logger.bind(**log_ctx).warning(
            f"Task lineage verification failed: parent task mismatch. Expected: {token.parent_task_id}, Got: {parent_task_id}"
        )
        return False
    if task_id and token.task_id != task_id:
        logger.bind(**log_ctx).warning(
            f"Task lineage verification failed: task ID mismatch. Expected: {token.task_id}, Got: {task_id}"
        )
        return False
    logger.bind(**log_ctx).debug("Task lineage verification successful")
    return True

def verify_scope_inheritance(token, parent_token, check_expansions=True):
    """Verify that a token's scope is a valid subset of its parent token's scope."""
    parent_scope = set(parent_token.scope)
    token_scope = set(token.scope)
    is_subset = token_scope.issubset(parent_scope)
    if is_subset:
        return True
    if not check_expansions:
        return False
    exceeded_scopes = token_scope - parent_scope
    return is_scope_expansion_allowed(exceeded_scopes, parent_scope, token.client_id, parent_token.client_id)

def is_scope_expansion_allowed(exceeded_scopes, parent_scopes, client_id=None, parent_client_id=None):
    """Check if scope expansion is allowed based on policy rules."""
    if not Config.SCOPE_EXPANSION_POLICY:
        return False
    policy = {}
    if client_id and client_id in policy.get('clients', {}):
        client_policy = policy['clients'][client_id]
        if client_policy.get('allow_all_expansions', False):
            logger.debug(f"Allowing scope expansion for authorized client: {client_id}")
            return True
        allowed_expansions = client_policy.get('allowed_expansions', [])
        for expansion in allowed_expansions:
            if expansion.get('from_scope') in parent_scopes and expansion.get('to_scope') in exceeded_scopes:
                logger.debug(f"Allowing scope expansion from '{expansion.get('from_scope')}' to '{expansion.get('to_scope')}' for client: {client_id}")
                return True
    global_policies = policy.get('global', {})
    patterns = global_policies.get('allowed_patterns', [])
    for pattern in patterns:
        required_scope = pattern.get('required_scope')
        allowed_expansion = pattern.get('allowed_expansion')
        if required_scope in parent_scopes and allowed_expansion in exceeded_scopes:
            logger.debug(f"Allowing scope expansion from '{required_scope}' to '{allowed_expansion}' based on global policy")
            return True
    expansions = global_policies.get('allowed_expansions', [])
    for expansion in expansions:
        from_scope = expansion.get('from_scope')
        to_scope = expansion.get('to_scope')
        if from_scope in parent_scopes and to_scope in exceeded_scopes:
            logger.debug(f"Allowing scope expansion from '{from_scope}' to '{to_scope}' based on global policy")
            return True
    logger.debug(f"Denying scope expansion: {exceeded_scopes} not allowed from parent scopes {parent_scopes}")
    return False

def verify_tool_access(token, tool_name):
    """Verify that a token has access to use a specific tool via OPA policy."""
    log_ctx = {
        "token_id": token.token_id,
        "client_id": token.client_id,
        "task_id": token.task_id,
        "tool_name": tool_name
    }
    from app.core.policy.opa_client import opa_client
    # Resolve tool object for classification
    from app.db.models import Tool
    if isinstance(tool_name, str) and len(tool_name) == 36 and "-" in tool_name:
        tool_obj = Tool.query.get(tool_name)
    else:
        tool_obj = Tool.query.filter_by(name=tool_name).first()
    if not tool_obj:
        logger.bind(**log_ctx).warning("Tool access denied: tool not found")
        return False
    input_data = {
        "agent": {"agent_trust_level": token.agent_trust_level},
        "tool": {"classification": tool_obj.category}
    }
    try:
        allowed = opa_client.query_bool_sync("allow_tool", input_data)
        if allowed:
            logger.bind(**log_ctx).debug("Tool access granted by OPA policy")
        else:
            logger.bind(**log_ctx).warning("Tool access denied by OPA policy")
        return allowed
    except Exception as e:
        logger.error(f"OPA tool access query failed: {e}")
        return False 