from fastapi import APIRouter, HTTPException, Body
from typing import Dict, List, Any, Optional
import uuid

from agentictrust.core.policy.opa_client import opa_client
from agentictrust.schemas.policies import (
    CreatePolicyRequest, UpdatePolicyRequest,
    PolicyResponse, CreatePolicyResponse,
    ListPoliciesResponse, BasicResponse,
    PolicyCheckRequest, PolicyCheckResponse
)

# Create router with prefix and tags
router = APIRouter(prefix="/api/policies", tags=["policies"])

# Helper to build OPA data path
def _policy_path(pid: str) -> str:
    return f"admin/policies/{pid}"

# ----------------- CRUD -----------------

@router.post("", status_code=201, response_model=CreatePolicyResponse)
async def create_policy(data: CreatePolicyRequest) -> CreatePolicyResponse:
    policy_id = str(uuid.uuid4())
    policy_obj: Dict[str, Any] = {
        "policy_id": policy_id,
        "name": data.name,
        "description": data.description,
        "scopes": data.scopes or [],
        "effect": data.effect,
        "priority": data.priority,
        "conditions": data.conditions or {},
    }
    try:
        opa_client.put_data(_policy_path(policy_id), policy_obj)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OPA sync failed: {e}")
    return {"message": "Policy created successfully", "policy": policy_obj}

@router.get("", response_model=ListPoliciesResponse)
async def list_policies() -> ListPoliciesResponse:
    policies = opa_client.get_data("admin/policies") or {}
    return {"policies": list(policies.values())}

@router.get("/{policy_id}", response_model=PolicyResponse)
async def get_policy(policy_id: str) -> PolicyResponse:
    pol = opa_client.get_data(_policy_path(policy_id))
    if not pol:
        raise HTTPException(status_code=404, detail="Policy not found")
    return pol

@router.put("/{policy_id}", response_model=CreatePolicyResponse)
async def update_policy(policy_id: str, data: UpdatePolicyRequest) -> CreatePolicyResponse:
    existing = opa_client.get_data(_policy_path(policy_id))
    if not existing:
        raise HTTPException(status_code=404, detail="Policy not found")
    updated = {**existing, **data.dict(exclude_unset=True)}
    try:
        opa_client.put_data(_policy_path(policy_id), updated)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OPA sync failed: {e}")
    return {"message": "Policy updated successfully", "policy": updated}

@router.delete("/{policy_id}", response_model=BasicResponse)
async def delete_policy(policy_id: str) -> BasicResponse:
    pol = opa_client.get_data(_policy_path(policy_id))
    if not pol:
        raise HTTPException(status_code=404, detail="Policy not found")
    opa_client.delete_data(_policy_path(policy_id))
    return {"message": "Policy deleted successfully"}

# ----------------- Policy Check -----------------

@router.post("/check", response_model=PolicyCheckResponse)
async def check_policy(data: PolicyCheckRequest = Body(...)) -> PolicyCheckResponse:
    """
    Check if a request is allowed based on authorization data.
    This endpoint proxies the request to OPA for policy decision.
    """
    # Extract auth and request data
    auth = data.auth.dict()
    request = data.request.dict()
    
    # Combine into the input format OPA expects
    input_data = {
        "user_id": auth.get("user_id"),
        "username": auth.get("username"),
        "department": auth.get("department"),
        "partner": auth.get("partner"),
        "scopes": auth.get("scopes", []),
        "action": request.get("action"),
        "resource": request.get("resource", {}),
        "token_id": auth.get("token_id"),
        "parent_token_id": auth.get("parent_token_id")
    }
    
    try:
        # Query OPA with the constructed input
        allowed = await opa_client.is_allowed(input_data)
        return {
            "allowed": allowed,
            "message": "Access granted" if allowed else "Access denied",
            "decision_id": str(uuid.uuid4())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Policy check failed: {str(e)}")
