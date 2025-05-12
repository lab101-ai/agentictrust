from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from agentictrust.core.registry import get_delegation_engine
from pydantic import BaseModel, Field
from agentictrust.core.policy.opa_client import opa_client

router = APIRouter(prefix="/api/delegations", tags=["delegations"])
engine = get_delegation_engine()

class DelegationCreate(BaseModel):
    principal_type: str = Field(..., pattern=r"^(user|agent)$")
    principal_id: str
    delegate_id: str
    scope: List[str]
    max_depth: int = 1
    constraints: Dict[str, Any] | None = None
    ttl_hours: int = 24

@router.post("/", response_model=Dict[str, Any])
async def create_delegation(body: DelegationCreate):
    # Run OPA policy enforcement BEFORE persisting the delegation
    allowed = await opa_client.is_allowed({
        "action": "create_delegation",
        "principal_type": body.principal_type,
        "principal_id": body.principal_id,
        "delegate_id": body.delegate_id,
        "scope": body.scope,
        "max_depth": body.max_depth,
        "constraints": body.constraints,
        "ttl_hours": body.ttl_hours,
    })
    if not allowed:
        raise HTTPException(status_code=403, detail="access_denied: OPA policy denied delegation creation")

    try:
        delegation = engine.create_grant(**body.dict())
        # Add OPA sync for new delegation grant
        try:
            opa_client.put_data(f"runtime/delegations/{delegation['grant_id']}", delegation)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OPA sync failed: {e}")
        return delegation
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

@router.delete("/{grant_id}")
async def delete_delegation(grant_id: str):
    try:
        engine.revoke_grant(grant_id)
        # Add OPA delete for removed delegation grant
        try:
            opa_client.delete_data(f"runtime/delegations/{grant_id}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OPA delete failed: {e}")
        return {"message": "revoked"}
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))

@router.get("/{grant_id}", response_model=Dict[str, Any])
async def get_delegation(grant_id: str):
    try:
        return engine.get_grant(grant_id)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))

@router.get("/principal/{principal_id}", response_model=List[Dict[str, Any]])
async def list_principal_delegations(principal_id: str):
    return engine.list_grants_for_principal(principal_id) 