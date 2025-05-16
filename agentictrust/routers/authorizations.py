"""FastAPI router for user↔agent authorization APIs."""
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from agentictrust.core.registry import get_authorization_engine
from agentictrust.schemas.user_agent_authorization import AuthorizationCreateRequest, AuthorizationOut
from agentictrust.core.policy.opa_client import opa_client

router = APIRouter(prefix="/api/authorizations", tags=["authorizations"])
engine = get_authorization_engine()


@router.post("", response_model=AuthorizationOut, status_code=201)
async def create_authorization(req: AuthorizationCreateRequest):
    # Optional: run OPA check
    allowed = await opa_client.is_allowed({
        "action": "create_authorization",
        "user_id": req.user_id,
        "agent_id": req.agent_id,
        "scopes": req.scopes,
    })
    if not allowed:
        raise HTTPException(status_code=403, detail="access_denied")

    try:
        auth = engine.create(user_id=req.user_id, agent_id=req.agent_id, scopes=req.scopes)
        # Sync to OPA data store
        try:
            opa_client.put_data(f"runtime/authorizations/{auth['authorization_id']}", auth)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OPA sync failed: {e}")
        return auth  # Pydantic will transform
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{authorization_id}")
async def revoke_authorization(authorization_id: str):
    try:
        engine.revoke(authorization_id)
        try:
            opa_client.delete_data(f"runtime/authorizations/{authorization_id}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OPA delete failed: {e}")
        return {"message": "revoked"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/user/{user_id}", response_model=List[AuthorizationOut])
async def list_user_authorizations(user_id: str):
    return engine.list_for_user(user_id)
