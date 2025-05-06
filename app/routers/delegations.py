from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from app.core.registry import get_delegation_engine
from pydantic import BaseModel, Field

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
    try:
        return engine.create_grant(**body.dict())
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

@router.delete("/{grant_id}")
async def delete_delegation(grant_id: str):
    try:
        engine.revoke_grant(grant_id)
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