from fastapi import APIRouter, HTTPException, Body, Request, Response, Depends
from fastapi.responses import RedirectResponse
from typing import Dict, Any, List
from agentictrust.core import get_user_engine
from agentictrust.core.policy.opa_client import opa_client
from agentictrust.core.auth.auth0 import oauth, verify_auth0_token, extract_user_from_claims
from agentictrust.schemas.users import Auth0UserRequest, TokenResponse, UserProfile
from agentictrust.core.users.engine import UserEngine
from agentictrust.utils.logger import logger
import json
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/users", tags=["users"])
engine = get_user_engine()

@router.post("", status_code=201)
async def create_user(data: dict = Body(...)) -> Dict[str, Any]:
    try:
        if not data.get("username") or not data.get("email"):
            raise ValueError("Username and email are required")
            
        user = engine.create_user(
            username=str(data.get("username")),
            email=str(data.get("email")),
            full_name=data.get("full_name"),
            hashed_password=data.get("hashed_password"),
            is_external=data.get("is_external", False),
            department=data.get("department"),
            job_title=data.get("job_title"),
            level=data.get("level"),
            scopes=data.get("scopes", []),
        )
        # Add OPA sync for new user
        try:
            opa_client.put_data(f"runtime/users/{user['user_id']}", user)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OPA sync failed: {e}")
        return {"message": "User created successfully", "user": user}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to create user")

@router.get("")
async def list_users() -> Dict[str, Any]:
    try:
        users = engine.list_users()
        return {"users": users}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to list users")

@router.get("/{user_id}")
async def get_user(user_id: str) -> Dict[str, Any]:
    try:
        return engine.get_user(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to get user")

@router.put("/{user_id}")
async def update_user(user_id: str, data: dict = Body(...)) -> Dict[str, Any]:
    try:
        updated = engine.update_user(user_id, data)
        # Add OPA sync for updated user
        try:
            opa_client.put_data(f"runtime/users/{user_id}", updated)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OPA sync failed: {e}")
        return {"message": "User updated successfully", "user": updated}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to update user")

@router.delete("/{user_id}")
async def delete_user(user_id: str) -> Dict[str, Any]:
    try:
        engine.delete_user(user_id)
        # Add OPA delete for removed user
        try:
            opa_client.delete_data(f"runtime/users/{user_id}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OPA delete failed: {e}")
        return {"message": "User deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to delete user")

@router.get("/login/auth0")
async def login_auth0(request: Request):
    """Redirect to Auth0 for authentication."""
    redirect_uri = request.url_for('auth0_callback')
    return await oauth.auth0.authorize_redirect(request, redirect_uri)

@router.get("/login/auth0/callback")
async def auth0_callback(request: Request):
    """Handle Auth0 callback and create/update user."""
    token = await oauth.auth0.authorize_access_token(request)
    user_info = await oauth.auth0.parse_id_token(request, token)
    
    auth0_id = user_info.get('sub')
    email = user_info.get('email')
    name = user_info.get('name')
    
    user = engine.find_user_by_auth0_id(auth0_id)
    
    if user:
        user.last_login = datetime.utcnow()
        if token.get('refresh_token'):
            user.refresh_token = token.get('refresh_token')
        engine.update_user(user.user_id, {
            'last_login': user.last_login,
            'refresh_token': user.refresh_token
        })
    else:
        user_data = Auth0UserRequest(
            auth0_id=auth0_id,
            email=email,
            full_name=name,
            auth0_metadata=user_info,
            social_provider='auth0'
        )
        user = engine.create_user_from_auth0(user_data)
    
    response = RedirectResponse(url="/dashboard")
    response.set_cookie(
        key="access_token",
        value=token['access_token'],
        httponly=True,
        secure=True,
        max_age=token['expires_in']
    )
    
    return response

@router.post("/auth0/token")
async def exchange_auth0_token(request: Request):
    """Exchange Auth0 token for AgenticTrust token."""
    try:
        data = await request.json()
        auth0_token = data.get('auth0_token')
        
        if not auth0_token:
            raise HTTPException(status_code=400, detail="Auth0 token is required")
        
        claims = await verify_auth0_token(auth0_token)
        user_data = extract_user_from_claims(claims)
        
        user = engine.find_user_by_auth0_id(user_data['auth0_id'])
        
        if not user:
            user_request = Auth0UserRequest(
                auth0_id=user_data['auth0_id'],
                email=user_data['email'],
                full_name=user_data['name'],
                auth0_metadata=user_data['metadata'],
                social_provider='auth0'
            )
            user = engine.create_user_from_auth0(user_request)
        
        from agentictrust.core.oauth.engine import OAuthEngine
        from agentictrust.schemas.oauth import TokenRequestClientCredentials, LaunchReason
        
        oauth_engine = OAuthEngine()
        
        token_request = TokenRequestClientCredentials(
            scope=["openid", "profile", "email"],
            launch_reason=LaunchReason.user_interactive,
            task_description="Auth0 user authentication",
            task_id=str(uuid.uuid4())
        )
        
        from agentictrust.db.models import Agent
        agent = Agent.query.filter_by(user_id=user.user_id).first()
        
        if not agent:
            from agentictrust.core import get_agent_engine
            agent_engine = get_agent_engine()
            agent = agent_engine.register_agent(
                agent_name=f"auth0-user-{user.username}",
                description="Auth0 authenticated user agent",
                agent_type="auth0_user",
                agent_model="auth0",
                agent_provider="auth0"
            )
        
        agent_data = agent.get('agent', {})
        credentials = agent.get('credentials', {})
        
        token_response = oauth_engine.issue_client_credentials(
            client_id=credentials.get('client_id'),
            client_secret=credentials.get('client_secret'),
            data=token_request,
            launched_by=user.user_id
        )
        
        return TokenResponse(**token_response)
    except Exception as e:
        logger.error(f"Error exchanging Auth0 token: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profile")
async def get_user_profile(request: Request):
    """Get user profile using Auth0 token."""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        token = auth_header.split(' ')[1]
        
        claims = await verify_auth0_token(token)
        user_data = extract_user_from_claims(claims)
        
        user = engine.find_user_by_auth0_id(user_data['auth0_id'])
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return UserProfile(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            department=user.department,
            job_title=user.job_title,
            is_external=user.is_external,
            scopes=[scope.scope_id for scope in user.scopes],
            auth0_metadata=user.get_auth0_metadata(),
            mfa_enabled=user.mfa_enabled,
            picture=user_data.get('picture')
        )
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
