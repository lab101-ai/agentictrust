from fastapi import APIRouter, HTTPException, Body, Depends
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from agentictrust.core import get_agent_engine
from agentictrust.core.policy.opa_client import opa_client
from agentictrust.schemas.agents import RegisterAgentRequest, ActivateAgentRequest, UpdateAgentRequest
from agentictrust.db.models.user_agent_authorization import UserAgentAuthorization
from agentictrust.schemas.user_agent_authorization import (
    CreateUserAgentAuthorizationRequest,
    UpdateUserAgentAuthorizationRequest,
    UserAgentAuthorizationResponse
)
from agentictrust.db import db_session
from agentictrust.utils.logger import logger

# Create router with prefix and tags
router = APIRouter(prefix="/api/agents", tags=["agents"])
engine = get_agent_engine()

@router.post("/users/{user_id}/authorizations", response_model=UserAgentAuthorizationResponse)
async def create_user_agent_authorization(
    user_id: str,
    request: CreateUserAgentAuthorizationRequest
):
    """Create a new user-agent authorization."""
    try:
        auth = UserAgentAuthorization.create(
            user_id=user_id,
            agent_id=request.agent_id,
            scopes=request.scopes,
            constraints=request.constraints,
            ttl_days=request.ttl_days
        )
        
        return UserAgentAuthorizationResponse(**auth.to_dict())
    except Exception as e:
        logger.error(f"Error creating user-agent authorization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{user_id}/authorizations", response_model=List[UserAgentAuthorizationResponse])
async def list_user_agent_authorizations(user_id: str):
    """List all agent authorizations for a user."""
    try:
        auths = UserAgentAuthorization.list_by_user(user_id)
        return [UserAgentAuthorizationResponse(**auth.to_dict()) for auth in auths]
    except Exception as e:
        logger.error(f"Error listing user-agent authorizations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{user_id}/authorizations/{authorization_id}", response_model=UserAgentAuthorizationResponse)
async def get_user_agent_authorization(user_id: str, authorization_id: str):
    """Get a specific user-agent authorization."""
    try:
        auth = UserAgentAuthorization.get_by_id(authorization_id)
        if not auth or auth.user_id != user_id:
            raise HTTPException(status_code=404, detail="Authorization not found")
        
        return UserAgentAuthorizationResponse(**auth.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user-agent authorization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/users/{user_id}/authorizations/{authorization_id}", response_model=UserAgentAuthorizationResponse)
async def update_user_agent_authorization(
    user_id: str,
    authorization_id: str,
    request: UpdateUserAgentAuthorizationRequest
):
    """Update a user-agent authorization."""
    try:
        auth = UserAgentAuthorization.get_by_id(authorization_id)
        if not auth or auth.user_id != user_id:
            raise HTTPException(status_code=404, detail="Authorization not found")
        
        auth.update(
            scopes=request.scopes,
            constraints=request.constraints,
            is_active=request.is_active,
            ttl_days=request.ttl_days
        )
        
        return UserAgentAuthorizationResponse(**auth.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user-agent authorization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/users/{user_id}/authorizations/{authorization_id}")
async def delete_user_agent_authorization(user_id: str, authorization_id: str):
    """Revoke a user-agent authorization."""
    try:
        auth = UserAgentAuthorization.get_by_id(authorization_id)
        if not auth or auth.user_id != user_id:
            raise HTTPException(status_code=404, detail="Authorization not found")
        
        auth.revoke()
        
        return {"message": "Authorization revoked successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking user-agent authorization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/register", status_code=201)
async def register_agent(data: RegisterAgentRequest) -> Dict[str, Any]:
    try:
        result = engine.register_agent(
            agent_name=data.agent_name,
            description=data.description,
            max_scope_level=data.max_scope_level,
            tool_ids=data.tool_ids,
            agent_type=data.agent_type,
            agent_model=data.agent_model,
            agent_version=data.agent_version,
            agent_provider=data.agent_provider,
        )
        # Add OPA sync for new agent
        agent = result.get('agent')
        if agent:
            try:
                opa_client.put_data(f"runtime/agents/{agent['client_id']}", agent)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"OPA sync failed: {e}")
        return {'message': 'Agent registered successfully', **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to register agent")

@router.post("/activate")
async def activate_agent(data: ActivateAgentRequest) -> Dict[str, Any]:
    try:
        result = engine.activate_agent(data.registration_token)
        return {'message': 'Agent activated successfully', **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to activate agent")

@router.get("/list")
async def list_agents() -> Dict[str, Any]:
    try:
        agents = engine.list_agents()
        return {'agents': agents}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to list agents")

@router.get("/{client_id}")
async def get_agent(client_id: str) -> Dict[str, Any]:
    try:
        return engine.get_agent(client_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to get agent")

@router.delete("/{client_id}")
async def delete_agent(client_id: str) -> Dict[str, Any]:
    try:
        engine.delete_agent(client_id)
        # Add OPA delete for removed agent
        try:
            opa_client.delete_data(f"runtime/agents/{client_id}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OPA delete failed: {e}")
        return {'message': 'Agent deleted successfully'}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to delete agent")

@router.get("/me")
async def get_current_agent():  # -> Dict[str, Any]
    """Get the current agent's details (using token authentication)."""
    # TODO: Implement auth dependency using the get_current_agent dependency
    # This will need to be updated once the FastAPI auth system is implemented
    # For now, returning not implemented to maintain API compatibility
    raise HTTPException(status_code=501, detail="Not implemented")

@router.get("/{client_id}/tools")
async def get_agent_tools(client_id: str) -> Dict[str, Any]:
    try:
        tools = engine.get_agent_tools(client_id)
        return {'tools': tools}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to get agent tools")

@router.post("/{client_id}/tools/{tool_id}")
async def add_tool_to_agent(client_id: str, tool_id: str) -> Dict[str, Any]:
    try:
        engine.add_tool_to_agent(client_id, tool_id)
        return {'message': 'Tool added to agent successfully'}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to add tool to agent")

@router.delete("/{client_id}/tools/{tool_id}")
async def remove_tool_from_agent(client_id: str, tool_id: str) -> Dict[str, Any]:
    try:
        engine.remove_tool_from_agent(client_id, tool_id)
        return {'message': 'Tool removed from agent successfully'}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to remove tool from agent")

@router.put("/{client_id}")
async def update_agent(client_id: str, data: UpdateAgentRequest) -> Dict[str, Any]:
    try:
        result = engine.update_agent(client_id, data.model_dump(exclude_unset=True))
        # Add OPA sync for updated agent
        agent = result.get('agent')
        if agent:
            try:
                opa_client.put_data(f"runtime/agents/{client_id}", agent)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"OPA sync failed: {e}")
        return {'message': 'Agent updated successfully', **result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to update agent")
