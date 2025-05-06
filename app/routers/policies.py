from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any, Optional
from app.core import get_policy_engine
from app.schemas.policies import (
    CreatePolicyRequest, UpdatePolicyRequest,
    PolicyResponse, CreatePolicyResponse,
    ListPoliciesResponse, BasicResponse
)

# Create router with prefix and tags
router = APIRouter(prefix="/api/policies", tags=["policies"])

engine = get_policy_engine()

@router.post("", status_code=201, response_model=CreatePolicyResponse)
async def create_policy(data: CreatePolicyRequest) -> CreatePolicyResponse:
    try:
        policy = engine.create_policy(
            name=data.name,
            description=data.description,
            scopes=data.scopes,
            effect=data.effect,
            priority=data.priority,
            conditions=data.conditions
        )
        return {'message': 'Policy created successfully', 'policy': policy}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create policy: {str(e)}")

@router.get("", response_model=ListPoliciesResponse)
async def list_policies() -> ListPoliciesResponse:
    try:
        policies = engine.list_policies()
        return {'policies': policies}
    except Exception:
        raise HTTPException(status_code=500, detail='Failed to list policies')

@router.get("/{policy_id}", response_model=PolicyResponse)
async def get_policy(policy_id: str) -> PolicyResponse:
    try:
        return engine.get_policy(policy_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail='Failed to get policy')

@router.put("/{policy_id}", response_model=CreatePolicyResponse)
async def update_policy(policy_id: str, data: UpdatePolicyRequest) -> CreatePolicyResponse:
    try:
        update_data = data.dict(exclude_unset=True)
        updated = engine.update_policy(policy_id, update_data)
        return {'message': 'Policy updated successfully', 'policy': updated}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail='Failed to update policy')

@router.delete("/{policy_id}", response_model=BasicResponse)
async def delete_policy(policy_id: str) -> BasicResponse:
    try:
        engine.delete_policy(policy_id)
        return {'message': 'Policy deleted successfully'}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail='Failed to delete policy')
