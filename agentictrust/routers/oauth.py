from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import RedirectResponse, JSONResponse
from typing import Dict, Any, Optional
from agentictrust.core.policy.opa_client import opa_client
from agentictrust.db.models.role import Role
from agentictrust.schemas.oauth import (
    TokenRequest,
    IntrospectRequest,
    RevokeRequest,
    TokenRequestClientCredentials,
    TokenRequestRefreshToken,
    TokenRequestAuthorizationCode,
    DelegationTokenRequest,
    DelegationTokenResponse,
    DelegationType,
)
# Use centralised OAuth engine
from agentictrust.core.registry import get_oauth_engine
from agentictrust.utils.logger import logger

engine = get_oauth_engine()

# Create router with prefix and tags
router = APIRouter(prefix="/api/oauth", tags=["oauth"])

@router.post("/token")
async def token_endpoint(data: TokenRequest, request: Request) -> Dict[str, Any]:
    """Token endpoint implementing client_credentials and refresh_token grants."""
    if isinstance(data, TokenRequestClientCredentials):
        try:
            return engine.issue_client_credentials(
                client_id=data.client_id,
                client_secret=data.client_secret,
                data=data,
            )
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            logger.error(f"Client-credentials issuance failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to issue token")
    
    elif isinstance(data, TokenRequestRefreshToken):
        try:
            return engine.refresh_token(
                refresh_token_raw=data.refresh_token,
                scope=data.scope,
            )
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            logger.error(f"Refresh grant failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to refresh token")

    elif isinstance(data, TokenRequestAuthorizationCode):
        try:
            token_obj, access_token, refresh_token = engine.exchange_code_for_token(
                client_id=data.client_id,
                code_plain=data.code,
                redirect_uri=data.redirect_uri,
                code_verifier=data.code_verifier,
            )
            # Commit happens inside engine; token_obj is fresh

            expires_in = int((token_obj.expires_at - token_obj.issued_at).total_seconds())
            response = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "expires_in": expires_in,
                "scope": token_obj.scopes.split(),
                "task_id": token_obj.task_id,
                "token_id": token_obj.token_id,
            }
            return response
        except ValueError as ve:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
        except Exception as e:
            logger.error(f"Auth code exchange failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to exchange authorization code")

    else:
         # This case should ideally not be reached due to Pydantic validation
         # Added check for exhaustiveness, though Pydantic should cover it.
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request data or unsupported grant type")

@router.post("/introspect")
async def introspect_endpoint(data: IntrospectRequest) -> Dict[str, Any]:
    """Token introspection endpoint (RFC 7662) via OAuthEngine."""
    if not data.token:
        raise HTTPException(status_code=400, detail="Missing token parameter")

    token_obj = engine.introspect(data.token)
    if not token_obj or not token_obj.is_valid():
        return {"active": False}
    
    payload = token_obj.to_dict()
    payload["active"] = True
    return payload

@router.post("/revoke")
async def revoke_endpoint(data: RevokeRequest) -> Dict[str, Any]:
    """Token revocation endpoint (RFC 7009) via OAuthEngine."""
    if not data.token:
        raise HTTPException(status_code=400, detail="Missing token parameter")
    # Introspect raw token to get token_id
    token_obj = engine.introspect(data.token)
    # per RFC, success even if token not found
    if not token_obj:
        return {"message": "Token revoked successfully"}
    # Revoke via engine
    engine.revoke(token_obj.token_id, revoke_children=data.revoke_children)
    return {"message": "Token revoked successfully"}

@router.post("/verify")
async def verify_token_endpoint(body: Dict[str, Any]) -> Dict[str, Any]:
    """Verify an access token and (optionally) its task lineage.

    This wraps core.oauth.utils.verify_token / verify_task_lineage providing a
    simple HTTP interface compliant with the Task-level OAuth verification
    requirement in the PRD.
    """
    from agentictrust.core.oauth.utils import verify_token as _verify_token, verify_task_lineage

    token_str: Optional[str] = body.get("token")
    if not token_str:
        raise HTTPException(status_code=400, detail="Missing 'token' in body")

    task_id: Optional[str] = body.get("task_id")
    parent_task_id: Optional[str] = body.get("parent_task_id")
    parent_token_str: Optional[str] = body.get("parent_token")
    allow_clock_skew: bool = body.get("allow_clock_skew", True)
    max_skew: int = body.get("max_clock_skew_seconds", 86400)

    token_obj = _verify_token(token_str, allow_clock_skew=allow_clock_skew, max_clock_skew_seconds=max_skew)
    if not token_obj:
        raise HTTPException(status_code=401, detail="invalid_token")

    parent_token_obj = None
    if parent_token_str:
        parent_token_obj = _verify_token(parent_token_str, allow_clock_skew=allow_clock_skew, max_clock_skew_seconds=max_skew)
        if not parent_token_obj:
            raise HTTPException(status_code=401, detail="invalid_parent_token")

    if any([task_id, parent_task_id, parent_token_obj]):
        if not verify_task_lineage(token_obj, parent_token=parent_token_obj, task_id=task_id, parent_task_id=parent_task_id):
            raise HTTPException(status_code=403, detail="task_lineage_invalid")

    return {
        "verified": True,
        "token_id": token_obj.token_id,
        "client_id": token_obj.client_id,
        "task_id": token_obj.task_id,
        "parent_task_id": token_obj.parent_task_id,
    }

# -------------------------------------------------------------------------
# Tool-access verification endpoint
# -------------------------------------------------------------------------
@router.post("/verify-tool-access")
async def verify_tool_access_endpoint(body: Dict[str, Any]) -> Dict[str, Any]:
    """Check whether the supplied token may invoke the given tool."""
    from agentictrust.core.oauth.utils import verify_token as _verify_token, verify_task_lineage, verify_tool_access as _verify_tool_access
    from agentictrust.core.policy.opa_client import opa_client

    token_str: Optional[str] = body.get("token")
    tool_name: Optional[str] = body.get("tool_name") or body.get("tool_id")
    if not token_str or not tool_name:
        raise HTTPException(status_code=400, detail="Missing required fields: 'token' and 'tool_name'")

    token_obj = _verify_token(token_str)
    if not token_obj or not token_obj.is_valid():
        raise HTTPException(status_code=401, detail="invalid_token")

    task_id: Optional[str] = body.get("task_id")
    parent_task_id: Optional[str] = body.get("parent_task_id")
    parent_token_str: Optional[str] = body.get("parent_token")

    parent_token_obj = None
    if parent_token_str:
        parent_token_obj = _verify_token(parent_token_str)
        if not parent_token_obj:
            raise HTTPException(status_code=401, detail="invalid_parent_token")

    if any([task_id, parent_task_id, parent_token_obj]):
        if not verify_task_lineage(token_obj, parent_token=parent_token_obj, task_id=task_id, parent_task_id=parent_task_id):
            raise HTTPException(status_code=403, detail="task_lineage_invalid")

    if not _verify_tool_access(token_obj, tool_name):
        raise HTTPException(status_code=403, detail="invalid_tool_access")

    # OPA policy enforcement for tool invocation
    tool_input = {
        "agent": {
            "client_id": token_obj.client_id,
            "agent_trust_level": token_obj.agent_trust_level,
            "status": "active" if token_obj.agent.is_active else "inactive",
        },
        "tool": {"name": tool_name},
        "action": "invoke_tool",
        "task_id": token_obj.task_id,
        "parent_task_id": token_obj.parent_task_id,
        "parent_token": parent_token_str,
    }
    if not await opa_client.is_allowed(tool_input):
        raise HTTPException(status_code=403, detail="access_denied: OPA policy denied tool access")

    return {
        "access": True,
        "token_id": token_obj.token_id,
        "tool": tool_name,
        "task_id": token_obj.task_id,
    }

@router.get("/agentinfo")
async def agentinfo(request: Request) -> Dict[str, Any]:
    """Agentinfo endpoint returns agent claims based on access token via OAuthEngine."""
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token_str = auth.split(" ", 1)[1]
    tok = engine.introspect(token_str)
    if not tok or not tok.is_valid():
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    # Return full token dict (includes OIDC-A + custom claims)
    return tok.to_dict()

@router.post("/check_token_access")
async def check_token_access(body: Dict[str, Any]) -> Dict[str, Any]:
    """Check if a token has access to a specific tool via OAuthEngine & policies."""
    token_str = body.get("token")
    tool_id = body.get("tool_id")
    if not token_str or not tool_id:
        raise HTTPException(status_code=400, detail="Missing required fields")
    tok = engine.introspect(token_str)
    if not tok or not tok.is_valid():
        return {"access": False, "error": "Token invalid or expired"}
    # Use policy/scope engine or utility
    from agentictrust.core.oauth.utils import verify_tool_access
    access = verify_tool_access(tok, tool_id)
    return {"access": access}

@router.get("/authorize")
async def authorize(request: Request) -> Any:
    """Authorization Code (PKCE) endpoint"""
    # Extract query params
    params = request.query_params
    resp = engine.authorize_request(
        response_type=params.get("response_type"),
        client_id=params.get("client_id"),
        redirect_uri=params.get("redirect_uri"),
        scope=params.get("scope"),
        state=params.get("state"),
        code_challenge=params.get("code_challenge"),
        code_challenge_method=params.get("code_challenge_method", "S256"),
    )
    if resp.get("consent_required"):
        # Return JSON for consent prompt (UI integration required)
        return JSONResponse(status_code=200, content=resp)
    # Auto-approved: perform redirect
    redirect_url = resp.get("redirect_url")
    return RedirectResponse(url=redirect_url)

@router.post("/delegate", response_model=DelegationTokenResponse)
async def delegate_token(request: DelegationTokenRequest):
    """Issue a delegated token from a human user or agent to an agent."""
    try:
        if request.delegation_type == DelegationType.HUMAN_TO_AGENT:
            response = await engine.process_human_delegation(request)
        elif request.delegation_type == DelegationType.AGENT_TO_AGENT:
            raise HTTPException(status_code=400, detail="Agent-to-agent delegation not yet implemented")
        else:
            raise HTTPException(status_code=400, detail="Invalid delegation type")
        
        return DelegationTokenResponse(**response)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing delegation request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/delegate/mfa", response_model=DelegationTokenResponse)
async def delegate_token_with_mfa(request: DelegationTokenRequest, mfa_challenge_id: str, mfa_code: str):
    """Issue a delegated token with MFA verification."""
    try:
        from agentictrust.core.auth.mfa import MFAManager
        
        # Extract user ID from token
        delegator_token = request.delegator_token
        delegator_claims = None
        user = None
        
        try:
            from agentictrust.core.auth.auth0 import verify_auth0_token, extract_user_from_claims
            delegator_claims = await verify_auth0_token(delegator_token, "auth0_domain")
            user_data = extract_user_from_claims(delegator_claims)
            
            from agentictrust.core.users.engine import UserEngine
            user_engine = UserEngine()
            user = user_engine.find_user_by_auth0_id(user_data['auth0_id'])
        except Exception:
            from agentictrust.core.oauth.utils import verify_token
            token_obj = verify_token(delegator_token)
            
            if not token_obj:
                raise HTTPException(status_code=400, detail="Invalid delegator token")
            
            from agentictrust.db.models.user import User
            user = User.query.filter_by(user_id=token_obj.delegator_sub).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        is_valid = MFAManager.verify_challenge(mfa_challenge_id, mfa_code, user.user_id)
        
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid MFA challenge or code")
        
        if request.delegation_type == DelegationType.HUMAN_TO_AGENT:
            response = await engine.process_human_delegation(request)
        elif request.delegation_type == DelegationType.AGENT_TO_AGENT:
            raise HTTPException(status_code=400, detail="Agent-to-agent delegation not yet implemented")
        else:
            raise HTTPException(status_code=400, detail="Invalid delegation type")
        
        return DelegationTokenResponse(**response)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing delegation request with MFA: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/authorize")
async def authorize_endpoint(
    response_type: str,
    client_id: str,
    redirect_uri: Optional[str] = None,
    scope: Optional[str] = None,
    state: Optional[str] = None,
    code_challenge: Optional[str] = None,
    code_challenge_method: Optional[str] = "S256",
) -> Dict[str, Any]:
    """Minimal OAuth 2.1 / PKCE *Authorization-Code* endpoint (auto-approve).

    This implementation issues an authorisation code immediately (no UI / consent)
    and responds with JSON that contains the `redirect_url` you would normally
    redirect to.  In production replace the JSON with a proper 302 redirect and
    add login / consent screens.
    """

    try:
        result = engine.authorize_request(
            response_type=response_type,
            client_id=client_id,
            redirect_uri=redirect_uri,
            scope=scope,
            state=state,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
        )
        # If human consent is required, return the JSON prompt
        if result.get("consent_required"):
            return result
        # Auto-approved: perform HTTP redirect to the client
        redirect_url = result.get("redirect_url")
        return RedirectResponse(url=redirect_url, status_code=302)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Authorization request failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process authorization request")

@router.post("/verify_with_rbac")
async def verify_token_with_rbac(request: Request):
    """Verify a token and check RBAC permissions."""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        token = auth_header.split(' ')[1]
        
        from agentictrust.core.oauth.utils import verify_token
        token_obj = verify_token(token)
        
        if not token_obj:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        data = await request.json()
        resource = data.get('resource')
        action = data.get('action')
        
        if not resource or not action:
            raise HTTPException(status_code=400, detail="Resource and action are required")
        
        from agentictrust.db.models.agent import Agent
        agent = Agent.query.get(token_obj.client_id)
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        input_data = {
            "agent": {
                "roles": [role.to_dict() for role in agent.roles]
            },
            "resource": resource,
            "action": action
        }
        
        allowed = opa_client.query_bool_sync("data.agentictrust.rbac.allow", input_data)
        
        if not allowed:
            raise HTTPException(status_code=403, detail="Permission denied")
        
        return {
            "token_id": token_obj.token_id,
            "client_id": token_obj.client_id,
            "scopes": token_obj.scopes.split(' ') if isinstance(token_obj.scopes, str) else token_obj.scopes,
            "expires_at": token_obj.expires_at.isoformat() if token_obj.expires_at else None,
            "is_valid": True,
            "rbac_check": "passed"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying token with RBAC: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
