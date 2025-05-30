from fastapi import APIRouter, HTTPException, Query
from typing import Text, Optional
from agentictrust.core import get_scope_engine
from agentictrust.schemas.scopes import (
    CreateScopeRequest,
    UpdateScopeRequest,
    ExpandRequest,
    ExpandResponse,
    ScopeRegistryResponse,
    ScopeResponse,
    CreateScopeResponse,
    ListScopesResponse,
    BasicResponse
)
from agentictrust.core.policy.opa_client import opa_client

# Create router with prefix and tags
router = APIRouter(prefix="/api/scopes", tags=["scopes"])

engine = get_scope_engine()

@router.post("", status_code=201, response_model=CreateScopeResponse)
async def create_scope(data: CreateScopeRequest):
    """Create a new scope."""
    try:
        params = data.dict()
        result = engine.create_scope(**params)
        # Add OPA sync for new scope
        try:
            opa_client.put_data(f"runtime/scopes/{result['scope_id']}", result)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OPA sync failed: {e}")
        return {'message': 'Scope created successfully', 'scope': result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=Text(e))
    except Exception:
        raise HTTPException(status_code=500, detail='Failed to create scope')

@router.get("", response_model=ListScopesResponse)
async def list_scopes(level: Optional[Text] = Query(None, description="Filter scopes by level")):
    """List all available scopes, optionally filtered by level."""
    try:
        scopes = engine.list_scopes(level)
        return {'scopes': scopes}
    except Exception:
        raise HTTPException(status_code=500, detail='Failed to list scopes')

@router.get("/{scope_id}", response_model=ScopeResponse)
async def get_scope(scope_id: Text):
    """Get scope details by ID."""
    try:
        return engine.get_scope(scope_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=Text(e))
    except Exception:
        raise HTTPException(status_code=500, detail='Failed to get scope')

@router.put("/{scope_id}", response_model=CreateScopeResponse)
async def update_scope(scope_id: Text, data: UpdateScopeRequest):
    """Update an existing scope."""
    try:
        updated = engine.update_scope(scope_id, data.dict(exclude_unset=True))
        # Add OPA sync for updated scope
        try:
            opa_client.put_data(f"runtime/scopes/{scope_id}", updated)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OPA sync failed: {e}")
        return {'message': 'Scope updated successfully', 'scope': updated}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=Text(e))
    except Exception:
        raise HTTPException(status_code=500, detail='Failed to update scope')

@router.delete("/{scope_id}", response_model=BasicResponse)
async def delete_scope(scope_id: Text):
    """Delete a scope by ID."""
    try:
        engine.delete_scope(scope_id)
        # Add OPA delete for removed scope
        try:
            opa_client.delete_data(f"runtime/scopes/{scope_id}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OPA delete failed: {e}")
        return {'message': 'Scope deleted successfully'}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=Text(e))
    except Exception:
        raise HTTPException(status_code=500, detail='Failed to delete scope')

@router.post("/expand", response_model=ExpandResponse)
async def expand_scopes(req: ExpandRequest):
    """Expand a list of scope names to include implied permissions."""
    expanded_list = engine.expand(req.scopes)
    return {"expanded": sorted(expanded_list)}

@router.get("/registry", response_model=ScopeRegistryResponse)
async def get_registry():
    """Get flattened metadata for all scopes."""
    try:
        items = engine.registry()
        return {"registry": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
